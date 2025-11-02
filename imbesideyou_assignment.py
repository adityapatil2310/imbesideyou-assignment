import os
import json
import pdfplumber
from openai import OpenAI
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ProfessorMatcherAgent:
    """
    An AI agent that finds the best professor matches based on a resume.

    This agent uses "tools" for:
    1. Parsing a resume (PDF)
    2. Scraping a faculty directory (NEEDS CUSTOMIZATION)
    3. Calling an LLM (ChatGPT) for scoring
    """

    def __init__(self, openai_api_key):
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found. Please set it as an environment variable.")
        self.client = OpenAI(api_key=openai_api_key)


    def _parse_resume(self, resume_path: str) -> str | None:
        if not resume_path.lower().endswith('.pdf'):
            print(f"Error: This agent is configured to read .pdf files. Received: {resume_path}")
            return None

        try:
            full_text = ""
            with pdfplumber.open(resume_path) as pdf:
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
            print("Resume parsed successfully.")
            return full_text
        except FileNotFoundError:
            print(f"Error: Resume file not found at path: {resume_path}")
            return None
        except Exception as e:
            print(f"Error parsing resume: {e}")
            return None

    # --- (MUST BE CUSTOMIZED) ---
    def _scrape_directory(self, directory_url: str) -> list[dict]:
        """
        Scrapes the main faculty directory for professor details.

        Every university directory has a different HTML structure.
        You must inspect the directory's HTML and update this function
        to correctly find the elements containing professor names,
        profile page URLs, and research interests.

        Customized for: https://www.cse.iitb.ac.in/people/faculty
        """
        print(f"Scraping directory: {directory_url}...")

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        driver = None

        professor_list = []
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

            driver.get(directory_url)

            print("Waiting for dynamic content to load...")
            wait = WebDriverWait(driver, 10)

            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.faculty-card")))

            prof_elements = driver.find_elements(By.CSS_SELECTOR, "div.faculty-card")
            print(f"Found {len(prof_elements)} professor elements.")

            if len(prof_elements) == 0:
                 print("Warning: Found 0 elements. Check selector or website structure.")

            for prof in prof_elements:
                try:
                    name = prof.find_element(By.CSS_SELECTOR, "h3.faculty-name").text.strip()

                    url = prof.find_element(By.CSS_SELECTOR, "div.faculty-info a").get_attribute("href")

                    research_interests_element = prof.find_element(By.CSS_SELECTOR, "div.faculty-research-interests")
                    research_interests = research_interests_element.text.strip() if research_interests_element else "N/A"

                    if not url.startswith('http'):
                        url = urljoin(directory_url, url)

                    professor_list.append({
                        "name": name,
                        "url": url,
                        "research_interests": research_interests
                    })
                except Exception as e:
                    print(f"Warning: Could not parse one professor element. Error: {e}")

            print(f"Successfully parsed {len(professor_list)} professors.")
            return professor_list

        except Exception as e:
            print(f"Error: Could not scrape directory URL with Selenium. {e}")
            return []

        finally:
            if driver:
                driver.quit()
                print("Browser has been closed.")



    def _get_match_score(self, resume_text: str, research_text: str) -> dict | None:
        """
        Uses the ChatGPT API to score the match between a resume and research text.
        Returns a dictionary: {"score": <int>, "research_summary": "<str>"}
        """
        system_prompt = (
            "You are an expert academic recruiter. Your task is to evaluate the match "
            "between a candidate's resume and a professor's research interests."
        )

        user_prompt = f"""
        Here is the candidate's resume:
        ---RESUME START---
        {resume_text}
        ---RESUME END---

        Here is the professor's research interests:
        ---RESEARCH START---
        {research_text}
        ---RESEARCH END---

        Please perform two tasks:
        1.  Briefly summarize the professor's research area in one or two sentences.
        2.  Provide a match score from 0 (no match) to 10 (perfect match) based on how
            well the candidate's skills and experience in their resume align with the
            professor's research area.

        Respond *only* in the following JSON format:
        {{
          "score": <score_number>,
          "research_summary": "<one_or_two_sentence_summary>"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )

            result = json.loads(response.choices[0].message.content)
            result['score'] = int(result['score'])
            return result

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None



    def run(self):
        print("--- Professor Matcher Agent Initialized ---")

        while True:
            directory_url = input("\n[Chat] Please paste the URL of the faculty directory: ")
            resume_path = input("[Chat] Please enter the local file path to your PDF resume: ")

            resume_text = self._parse_resume(resume_path)
            if not resume_text:
                print("[Chat] I couldn't read the resume. Let's try again.")
                continue

            all_professors = self._scrape_directory(directory_url)
            if not all_professors:
                print("[Chat] I couldn't find any professors. Check the URL or my `_scrape_directory` tool code.")
                continue

            scored_professors = []
            for i, prof in enumerate(all_professors):
                print(f"\nProcessing {i+1}/{len(all_professors)}: {prof['name']}...")

                score_data = self._get_match_score(resume_text, prof['research_interests'])
                if not score_data:
                    continue

                scored_professors.append({
                    "name": prof['name'],
                    "research_interests": prof['research_interests'],
                    "score": score_data['score']
                })


            if not scored_professors:
                print("[Chat] I wasn't able to score any professors.")
                continue

            print("\n[Chat] All professors processed! Ranking results...")

            sorted_profs = sorted(scored_professors, key=lambda x: x['score'], reverse=True)

            print("\n--- TOP 10 PROFESSOR MATCHES ---")
            for i, prof in enumerate(sorted_profs[:10]):
                print(f"\n#{i+1}: {prof['name']}")
                print(f"  - Research Area: {prof['research_interests']}")
                print(f"  - Match Score: {prof['score']}/10")

            if input("\n[Chat] Would you like to check another directory? (y/n): ").lower() != 'y':
                print("[Chat] Goodbye!")
                break

if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set it before running: export OPENAI_API_KEY='your_key_here'")
    else:
        agent = ProfessorMatcherAgent(openai_api_key=api_key)
        agent.run()