import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin

class JobScraperWithKPI:
    def __init__(self):
        self.base_url = "https://www.free-work.com"
        self.jobs_list = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def count_task_items(self, html_content):
        """Compte les éléments de liste dans la description"""
        soup = BeautifulSoup(html_content, 'html.parser')
        lists = soup.find_all(['ul', 'ol'])
        task_items = 0
        for list_elem in lists:
            items = list_elem.find_all('li', recursive=False)
            task_items += len(items)
        return task_items
    
    def extract_salary_value(self, salary_text):
        """Extrait valeur numérique du salaire"""
        if not salary_text or salary_text == 'N/C':
            return None
        
        matches = re.findall(r'£?([\d,]+k?|[\d,]+)', salary_text.replace('-', ' ').lower())
        values = []
        for match in matches:
            value = match.replace(',', '').replace('k', '')
            try:
                num = float(value) * 1000 if 'k' in match.lower() else float(value)
                values.append(num)
            except:
                continue
        
        return round(sum(values) / len(values), 2) if values else None
    
    def extract_salary(self, sidebar_div):
        """extraire salaire sidebar"""
        if not sidebar_div:
            return 'N/C'
        
        pay_rate_section = sidebar_div.find('span', string=re.compile(r'(Pay|Rate)', re.I))
        if pay_rate_section:
            salary_span = pay_rate_section.find_next_sibling('span')
            if salary_span:
                salary_text = salary_span.find('span', class_='text-sm')
                if salary_text:
                    return salary_text.get_text(strip=True)
        return 'N/C'
    
    def make_absolute_link(self, href):
        """Convertit lien relatif en absolu"""
        if not href:
            return 'N/C'
        if href.startswith('http'):
            return href
        if self.base_url.endswith('/') and href.startswith('/'):
            return self.base_url[:-1] + href
        elif not self.base_url.endswith('/') and not href.startswith('/'):
            return self.base_url + '/' + href
        return self.base_url + href
    
    def scrape_job_list(self, url, max_pages=3):
        for page in range(1, max_pages + 1):
            current_url = f"{url}&page={page}" if page > 1 else url
            
            try:
                response = requests.get(current_url, headers=self.headers, timeout=15)
                soup = BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                print(f"Erreur page {page}: {e}")
                continue
            
            # ✅ Conteneurs job identiques
            job_containers = soup.find_all('div', class_=re.compile(r'mb-4.*rounded-lg.*bg-white.*shadow'))
            
            for container in job_containers:
                job_data = self.extract_job_basic_info(container)
                if job_data['titre'] != 'N/C':
                    self.jobs_list.append(job_data)
                    salaire_display = job_data['salaire'] if job_data['salaire'] != 'N/C' else 'N/C'
                    print(f"✓ {job_data['titre'][:50]} | {salaire_display}")
            
            print(f"Page {page}: {len(job_containers)} job trouvé")
            time.sleep(2)
    
    def extract_job_basic_info(self, container):
        
        job = {
            'titre': 'N/C', 'entreprise': 'N/C', 'localisation': 'N/C',
            'salaire': 'N/C', 'salaire_num': None, 'type_contrat': 'N/C',
            'date_publication': 'N/C', 'description': 'N/C',
            'competences': 'N/C', 'experience': 'N/C', 'nombre_taches': 0,
            'kpi_salaire_taches': None, 'lien': 'N/C'
        }
        
        title_elem = container.find(['h2', 'h3'], class_=re.compile(r'font-semibold.*text-xl|text-lg'))
        if title_elem:
            title_link = title_elem.find('a')
            if title_link:
                job['titre'] = title_link.get_text(strip=True)
                href = title_link.get('href')
                job['lien'] = self.make_absolute_link(href)
                job['description'] = job['lien']  
        
        # ENTREPRISE
        company_elem = container.find('div', class_='font-bold')
        if company_elem:
            job['entreprise'] = company_elem.get_text(strip=True)
        
        # SALAIRE 
        sidebar = container.find('div', class_=re.compile(r'lg:w-64.*bg-gray-50'))
        job['salaire'] = self.extract_salary(sidebar)
        if job['salaire'] != 'N/C':
            job['salaire_num'] = self.extract_salary_value(job['salaire'])
        
        # Type contrat
        contract_tags = container.find_all('span', class_=re.compile(r'.*tag.*'))
        if contract_tags:
            job['type_contrat'] = contract_tags[0].get_text(strip=True)
        
        return job
    
    def scrape_job_details(self, job_data):
        """Détails supplémentaires (optionnel)"""
        if job_data['lien'] == 'N/C':
            return job_data
        
        try:
            response = requests.get(job_data['lien'], headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Description
            desc_elem = soup.find('div', class_=re.compile(r'prose-content|html-renderer|job-description'))
            if desc_elem:
                job_data['description'] = desc_elem.get_text(strip=True)[:2000]
                job_data['nombre_taches'] = self.count_task_items(str(desc_elem))
                
            # Compétences
            skill_links = soup.find_all('a', href=re.compile(r'/skills/'))
            skills = [s.get_text(strip=True) for s in skill_links[:15]]
            if skills:
                job_data['competences'] = ', '.join(set(skills))
            time.sleep(1)
        except:
            pass
        
        return job_data
    
    def calculate_kpi(self):
        """Calcule KPI"""
        for job in self.jobs_list:
            if job['salaire_num'] and job['nombre_taches']:
                job['kpi_salaire_taches'] = round(job['nombre_taches'] / job['salaire_num'] * 10000, 4)
    
    def save_to_csv(self, filename='jobs_with_kpi.csv'):
        """Sauvegarde + stats"""
        df = pd.DataFrame(self.jobs_list)
        columns = ['titre', 'entreprise', 'salaire', 'salaire_num', 'type_contrat', 
                  'lien', 'nombre_taches', 'kpi_salaire_taches', 'competences']
        df = df[[col for col in columns if col in df.columns]]
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\n{len(df)} jobs → {filename}")
        
        # Stats salaires
        with_salary = df[df['salaire_num'].notna()]
        if len(with_salary) > 0:
            print(f"{len(with_salary)} jobs trouvé avec salaire")
            print(f"   Salaire moyen: £{with_salary['salaire_num'].mean():,.0f}")
            print(f"   Salaire median: £{with_salary['salaire_num'].median():,.0f}")


if __name__ == "__main__":
    scraper = JobScraperWithKPI()
    url = "https://www.free-work.com/en-gb/tech-it/jobs?locations=gb~~~"
    
    print("FREE-WORK JOB SCRAPER\n")
    
    print("Scraping liste...")
    scraper.scrape_job_list(url, max_pages=1)
    
    print(f"\n Détails ({len(scraper.jobs_list)} jobs)...")
    for i, job in enumerate(scraper.jobs_list, 1):
        scraper.jobs_list[i-1] = scraper.scrape_job_details(job)
    
    print("\n KPI...")
    scraper.calculate_kpi()
    
    print("\n Sauvegarde...")
    scraper.save_to_csv()
    
