import requests
import time
import csv
import os

ACCESS_TOKEN = "YOUR_HH_TOKEN" # инструкиця по получению токена находится в readme
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

TEST_VACANCIES_FILE = "vacancies_with_tests.csv"
APPLIED_VACANCIES_FILE = "applied_vacancies.csv"

# Черный список работадателей
BLACKLIST = ["Company 1", "Company 2", "Company 1"]

# Функция загрузки ID вакансий из файла
def load_vacancies_from_file(filename):
    vacancy_ids = set()
    if os.path.exists(filename):
        with open(filename, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)  # Пропускаем заголовок
            for row in reader:
                vacancy_ids.add(row[0])
    return vacancy_ids

# Функция записи вакансий в файл
def save_vacancy_to_file(filename, vacancy_id, vacancy_data):
    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([vacancy_id] + vacancy_data)

# Загружаем уже обработанные вакансии
applied_vacancies = load_vacancies_from_file(APPLIED_VACANCIES_FILE)
test_vacancies = load_vacancies_from_file(TEST_VACANCIES_FILE)

# Получаем ID резюме
resume_response = requests.get("https://api.hh.ru/resumes/mine", headers=HEADERS)
resume_id = None

if resume_response.status_code == 200:
    resumes = resume_response.json().get("items", [])
    if resumes:
        resume_id = resumes[0]["id"]
        print(f"📄 Найдено резюме: {resume_id}")
    else:
        print("⚠️ Нет доступных резюме.")
        exit()
else:
    print("❌ Ошибка при получении резюме:", resume_response.text)
    exit()

# Функция проверки работодателя по черному списку
def is_blacklisted(employer_name):
    if employer_name is None:
        return False  
    return any(word.lower() in employer_name.lower() for word in BLACKLIST)

# Флаг, ограничивающий отклики при достижении лимита
apply_limit_reached = False

# Основной цикл
while True:
    page = 0  # Начинаем с первой страницы
    total_pages = 1  # Количество страниц (обновится после первого запроса)

    while page < total_pages:
        params = {
            "text": '"Вакансия 1" OR "Вакансия 2" OR "Вакансия 3"', # Вписать рассматриваемые позиции
            "area": 113,  # Россия
            "schedule": "remote",
            "only_with_salary": False,
            "per_page": 20,  # Ограничиваем до 20 вакансий на страницу для теста
            "page": page,  # Перебираем страницы
        }

        print(f"🔍 Отправка запроса: страница {page + 1}")

        response = requests.get("https://api.hh.ru/vacancies", headers=HEADERS, params=params)

        if response.status_code != 200:
            print("❌ Ошибка при поиске вакансий:", response.text)
            break

        data = response.json()
        vacancies = data.get("items", [])
        total_pages = data.get("pages", 1)  # Количество страниц

        if not vacancies:
            print("🚫 Вакансии закончились.")
            break

        for vacancy in vacancies:
            vacancy_id = vacancy["id"]
            vacancy_name = vacancy["name"]
            employer_name = vacancy.get("employer", {}).get("name", "Не указано")

            if is_blacklisted(employer_name):
                print(f"🚫 Вакансия '{vacancy_name}' от '{employer_name}' в черном списке. Пропущена.")
                continue

            if vacancy_id in applied_vacancies:
                print(f"🔄 Вакансия '{vacancy_name}' уже обработана ранее. Пропущена.")
                continue

            if vacancy.get("has_test", False):
                if vacancy_id not in test_vacancies:
                    print(f"📝 Вакансия '{vacancy_name}' требует теста. Записана в таблицу.")
                    save_vacancy_to_file(TEST_VACANCIES_FILE, vacancy_id, [
                        vacancy_name,
                        employer_name,
                        vacancy["alternate_url"]
                    ])
                    test_vacancies.add(vacancy_id)
                else:
                    print(f"🔁 Вакансия '{vacancy_name}' с тестом уже записана ранее. Пропускаем.")
                continue  

            if apply_limit_reached:
                print("⏳ Лимит откликов достигнут. Пропускаем отправку откликов.")
                continue

            # Отправляем отклик
            cover_letter = f"""Здравствуйте!

Меня заинтересовала вакансия "{vacancy_name}", так как она отлично соответствует моему опыту и профессиональным интересам.""" # дополнить шаблонное сопроводительное письмо
            
            apply_response = requests.post("https://api.hh.ru/negotiations", headers=HEADERS, params={
                "vacancy_id": vacancy_id,
                "resume_id": resume_id,
                "message": cover_letter,
            })

            if apply_response.status_code in [200, 201]:
                print(f"✅ Успешно отправлен отклик на вакансию: {vacancy_name}")
                save_vacancy_to_file(APPLIED_VACANCIES_FILE, vacancy_id, [])
                applied_vacancies.add(vacancy_id)
            else:
                error_data = apply_response.json()
                if "limit_exceeded" in str(error_data):
                    print("⚠️ Достигнут дневной лимит откликов! Остановлена отправка новых откликов.")
                    apply_limit_reached = True
                else:
                    print(f"❌ Ошибка при отклике: {apply_response.text}")

            time.sleep(5)  # Добавляем паузу между откликами

        page += 1  # Переход на следующую страницу
        print(f"📄 Обработана страница {page} из {total_pages}")

    print("⌛ Ожидание перед следующим циклом...")
    time.sleep(60)
