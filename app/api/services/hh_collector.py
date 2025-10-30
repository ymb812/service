import requests
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class HHruMassCollector:
    def __init__(self, output_dir: str = "hh_vacancies_data"):
        self.base_url = "https://api.hh.ru"
        self.output_dir = output_dir
        self.requests_per_second = 10
        self.delay_between_requests = 1.0 / self.requests_per_second
        
        # Список популярных IT-профессий для дополнительного поиска
        self.popular_it_professions = [
            "Python", "Java", "JavaScript", "C++", "C#", "PHP", "Ruby",
            "Go", "Swift", "Kotlin", "TypeScript", "Scala", "Rust",
            "DevOps", "Data Science", "Machine Learning", "AI",
            "Frontend", "Backend", "Fullstack", "Mobile Developer",
            "Data Engineer", "Data Analyst", "BI Analyst", "Big Data",
            "QA", "Testing", "Automation", "Manual Testing",
            "Security", "Cybersecurity", "Network", "System Administrator",
            "Cloud", "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes",
            "SQL", "Database", "PostgreSQL", "MySQL", "MongoDB",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask",
            "Spring", "Laravel", "Unity", "Game Development"
        ]
        
        os.makedirs(self.output_dir, exist_ok=True)
    
    def make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Выполнение запроса с соблюдением ограничений по частоте"""
        time.sleep(self.delay_between_requests)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка запроса к {url}: {e}")
            return {}
    
    def get_all_professional_roles(self) -> List[Dict[str, Any]]:
        """Получение всех профессиональных ролей с hh.ru"""
        print("Получаем список профессиональных ролей...")
        data = self.make_request("professional_roles")
        
        roles = []
        if 'categories' in data:
            for category in data['categories']:
                roles.extend(category.get('roles', []))
        
        print(f"Найдено профессиональных ролей: {len(roles)}")
        return roles
    
    def get_vacancy_count_for_role(self, role_id: str, role_name: str) -> int:
        """Получение количества вакансий для профессиональной роли"""
        params = {
            'professional_role': role_id,
            'area': 113,  # Россия
            'per_page': 1,
            'page': 0,
            'only_with_salary': True
        }
        
        data = self.make_request("vacancies", params)
        count = data.get('found', 0)
        
        print(f"Роль '{role_name}': {count} вакансий")
        return count
    
    def extract_essential_fields(self, vacancy: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает только необходимые поля из вакансии"""
        essential = {}
        
        # Общая информация
        essential['id'] = vacancy.get('id')
        essential['name'] = vacancy.get('name')
        essential['description'] = vacancy.get('description')
        
        # Профессиональная информация
        essential['professional_roles'] = vacancy.get('professional_roles', [])
        essential['key_skills'] = [skill.get('name') for skill in vacancy.get('key_skills', [])]
        essential['specializations'] = vacancy.get('specializations', [])
        essential['experience'] = vacancy.get('experience', {})
        
        # Условия работы
        essential['salary'] = vacancy.get('salary')
        essential['employment'] = vacancy.get('employment', {})
        essential['schedule'] = vacancy.get('schedule', {})

        return essential
    
    def collect_vacancies_for_role(self, role_id: str, role_name: str, target_count: int = 10) -> List[Dict[str, Any]]:
        """Сбор вакансий для конкретной профессиональной роли"""
        print(f"Собираем вакансии для '{role_name}' (цель: {target_count})")
        
        vacancies = []
        page = 0
        per_page = min(100, target_count)
        
        while len(vacancies) < target_count:
            params = {
                'professional_role': role_id,
                'area': 113,
                'per_page': per_page,
                'page': page,
                'only_with_salary': True
            }
            
            data = self.make_request("vacancies", params)
            items = data.get('items', [])
            
            if not items:
                break
            
            for item in items:
                if len(vacancies) >= target_count:
                    break
                
                vacancy_id = item['id']
                detailed_vacancy = self.get_vacancy_details(vacancy_id)
                
                if detailed_vacancy:
                    essential_fields = self.extract_essential_fields(detailed_vacancy)
                    vacancies.append(essential_fields)
                    
                    print(f"Собрано вакансий для '{role_name}': {len(vacancies)}/{target_count}")
            
            page += 1
            
            pages = data.get('pages', 0)
            if page >= pages:
                break
        
        return vacancies
    
    def search_vacancies_by_text(self, profession: str, target_count: int = 10) -> List[Dict[str, Any]]:
        """Поиск вакансий по текстовому запросу"""
        print(f"Текстовый поиск вакансий для '{profession}'...")
        
        vacancies = []
        page = 0
        per_page = min(100, target_count)
        
        while len(vacancies) < target_count:
            params = {
                'text': profession,
                'area': 113,
                'per_page': per_page,
                'page': page,
                'only_with_salary': True,
                'search_field': 'name'
            }
            
            data = self.make_request("vacancies", params)
            items = data.get('items', [])
            
            if not items:
                break
            
            for item in items:
                if len(vacancies) >= target_count:
                    break
                
                vacancy_id = item['id']
                detailed_vacancy = self.get_vacancy_details(vacancy_id)
                
                if detailed_vacancy:
                    essential_fields = self.extract_essential_fields(detailed_vacancy)
                    vacancies.append(essential_fields)
                    
                    print(f"Собрано вакансий для '{profession}': {len(vacancies)}/{target_count}")
            
            page += 1
            
            pages = data.get('pages', 0)
            if page >= pages:
                break
        
        return vacancies
    
    def get_vacancy_details(self, vacancy_id: str) -> Optional[Dict[str, Any]]:
        """Получение детальной информации о вакансии"""
        return self.make_request(f"vacancies/{vacancy_id}")
    
    def save_all_vacancies_to_json(self, all_vacancies: List[Dict[str, Any]], filename: str):
        """Сохранение всех вакансий в один JSON файл"""
        data = {
            "metadata": {
                "collection_time": datetime.now().isoformat(),
                "source": "hh.ru",
                "total_vacancies": len(all_vacancies),
                "vacancies_per_profession": 10,
                "version": "2.0"
            },
            "vacancies": all_vacancies
        }
        
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Все данные сохранены в {filepath}")
    
    def collect_all_vacancies(self):
        """Сбор всех вакансий (по ролям и IT-профессиям) в один файл"""
        print("=== НАЧАЛО СБОРА ВСЕХ ВАКАНСИЙ ===")
        start_time = time.time()
        
        all_vacancies = []
        statistics = {
            'roles_processed': 0,
            'it_professions_processed': 0,
            'total_collected': 0
        }
        
        # 1. Сбор по всем профессиональным ролям
        print("\n--- Сбор по профессиональным ролям ---")
        roles = self.get_all_professional_roles()
        
        for role in roles:
            role_id = role['id']
            role_name = role['name']
            
            # Получаем количество вакансий для статистики
            vacancy_count = self.get_vacancy_count_for_role(role_id, role_name)
            
            if vacancy_count > 0:
                role_vacancies = self.collect_vacancies_for_role(role_id, role_name, 10)
                all_vacancies.extend(role_vacancies)
                statistics['roles_processed'] += 1
                statistics['total_collected'] = len(all_vacancies)
                
                print(f"Прогресс по ролям: {statistics['roles_processed']}/{len(roles)} ролей, {len(all_vacancies)} вакансий")
        
        # 2. Сбор по IT-профессиям через текстовый поиск
        print("\n--- Сбор по IT-профессиям ---")
        for profession in self.popular_it_professions:
            profession_vacancies = self.search_vacancies_by_text(profession, 10)
            all_vacancies.extend(profession_vacancies)
            statistics['it_professions_processed'] += 1
            statistics['total_collected'] = len(all_vacancies)
            
            print(f"Прогресс по IT: {statistics['it_professions_processed']}/{len(self.popular_it_professions)} профессий, {len(all_vacancies)} вакансий")
        
        # 3. Сохраняем все вакансии в один файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hh_all_vacancies_{timestamp}.json"
        
        self.save_all_vacancies_to_json(all_vacancies, filename)
        
        # Итоговая статистика
        elapsed_time = time.time() - start_time
        print(f"\n=== СБОР ВСЕХ ВАКАНСИЙ ЗАВЕРШЕН ===")
        print(f"Общее время: {elapsed_time:.2f} секунд")
        print(f"Итого собрано вакансий: {len(all_vacancies)}")
        print(f"Обработано ролей: {statistics['roles_processed']}")
        print(f"Обработано IT-профессий: {statistics['it_professions_processed']}")
        print(f"Скорость сбора: {len(all_vacancies) / elapsed_time:.2f} вакансий/секунду")
        
        return all_vacancies

def main():
    """Пример использования"""
    collector = HHruMassCollector()
    
    # Сбор всех вакансий в один файл
    all_vacancies = collector.collect_all_vacancies()
    
    print(f"\n=== ИТОГИ ===")
    print(f"Всего собрано вакансий: {len(all_vacancies)}")
    print("Все данные сохранены в единый JSON-файл")

if __name__ == "__main__":
    main()
