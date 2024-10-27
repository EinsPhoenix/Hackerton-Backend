import google.generativeai as genai
import json
import logging
import re
from dotenv import load_dotenv
import os
import random
import time


load_dotenv()
json_file_path = "usage_data.json"
logger = logging.getLogger(__name__)


class GenerateResponse:
    def __init__(self):
     
        load_dotenv()
        self.api_keys = [
            os.getenv(f"GOOGLE_API_KEY_{i}")
            for i in range(1, 5)
            if os.getenv(f"GOOGLE_API_KEY_{i}")
        ]

        if not self.api_keys:
            raise ValueError("Keine gültigen API-Schlüssel gefunden")

    def select_random_api_key(self):
        self.API_KEY = random.choice(self.api_keys)
        genai.configure(api_key=self.API_KEY)
        print(f"Verwendeter API-Key: {self.API_KEY}")

    def _generate_content(self, prompt):
        self.select_random_api_key()
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        """Helper function to generate content using the generative model."""

        def attempt_generation():
            response = self.model.generate_content(prompt)
            logger.info(f"Generated result: {response.text}")

            # Verwendete tokens
            print(type(response.usage_metadata))
            print(self.API_KEY)
            self.document_usage(self.API_KEY, response.usage_metadata)

            cleaned_response = re.search(r"{.*}", response.text, re.DOTALL)
            if cleaned_response:
                json_text = cleaned_response.group(0)
                return json.loads(json_text.encode("utf-8").decode("utf-8"))
            else:
                logger.error("No valid JSON found in the response.")
                return {"error": "No valid JSON found in the response."}

        # Erster Versuch
        try:
            return attempt_generation()

        except Exception as e:
            logger.error(f"Error generating content (first attempt): {e}")
            self.track_error(self.API_KEY)
            self.select_random_api_key()
            time.sleep(5)

            try:
                return attempt_generation()

            except Exception as e:
                logger.error(f"Error generating content (second attempt): {e}")
                self.track_error(self.API_KEY)
                return {"error": str(e)}

    def track_error(self, api_key):
        """Track errors for the specified API key."""
        if os.path.exists(json_file_path):
            with open(json_file_path, "r") as json_file:
                data = json.load(json_file)
        else:
            data = {"usage_API": {}}

        if api_key not in data["usage_API"]:
            data["usage_API"][api_key] = {"anfragen": [], "errors": 0}

        data["usage_API"][api_key]["errors"] += 1

        with open(json_file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        print(f"Error for API Key {api_key} tracked successfully.")

    def document_usage(self, api_key, usage_data):
        extracted_usage_data = {
            "prompt_token_count": usage_data.prompt_token_count,
            "candidates_token_count": usage_data.candidates_token_count,
            "total_token_count": usage_data.total_token_count,
        }

        if os.path.exists(json_file_path):
            with open(json_file_path, "r") as json_file:
                data = json.load(json_file)
        else:
            data = {"usage_API": {}}

        if api_key not in data["usage_API"]:
            data["usage_API"][api_key] = {"anfragen": [], "errors": 0}

        data["usage_API"][api_key]["anfragen"].append(extracted_usage_data)

        with open(json_file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        print(f"Daten erfolgreich in {json_file_path} erweitert.")

    def create_quiz(self, input_text, lang):
        prompt = f"""
            Generate 5-8 quiz questions based on the following text, ensuring that the questions cover various aspects throughout the entire content. 
            Avoid conflating names and roles of individuals with company names. 
            Return only a JSON in the following format:

            {{
                "questions": [
                    "Question1",
                    "Question2",
                    "Question3",
                    "Question4",
                    "Question5",
                    "Question6"
                    ...
                ]
            }}

            Here is the text on which the questions should be based:\n\n{input_text}\n\n,
            Output the text in: \n\n{lang}\n\n
        """
        questions_json = self._generate_content(prompt)
        if "error" in questions_json:
            return {"error": "Failed to generate questions"}
        return questions_json

    def check_answers(self, input_text, questions, answers, lang):
        prompt = f"""
            Your a Teacher now.
            I have a set of questions based on the following text: \n\n{input_text}\n\n. 
            These are the questions: \n\n{questions}\n\n. 
            Below are my answers:\n\n{answers}\n\n.

            Your task is to evaluate each answer and assign 1 point for every fully correct answer. 
            If an answer is incorrect or partially correct, assign 0 points. 
            Be careful not to conflate individual names with company names.
            And provide the correct total_points. Also when the input from answers is not answered it is automaticly false.
            Check your answers multiple times!

            Provide feedback in this format:

            - If the answer is correct, simply confirm it: "Your answer was correct."
            - If the answer is incorrect or partially correct, explain why, then provide the correct answer: "Your answer was incorrect. The correct answer is..."
            - When the answer from the user is "not answered" the answer is incorect! And you have to correct it

            Return the results as a JSON object with this structure:
            {{
                "score": total_points,
                "questions": [
                    "{{question_1}}: Your answer was correct/incorrect. {{correct_answer_if_needed}}",
                    "{{question_2}}: Your answer was correct/incorrect. {{correct_answer_if_needed}}",
                    "...",
                    "{{question_n}}: Your answer was correct/incorrect. {{correct_answer_if_needed}}"
                ]
            }}

            Output the text in: \n\n{lang}\n\n
        """
        answers_json = self._generate_content(prompt)
        if "error" in answers_json:
            return {"error": "Failed to check answers"}
        return answers_json

    def generate_random_top(self, input_text, questions, lang):
        prompt = f"""
            I have a set of questions based on the following text: \n\n{input_text}\n\n. 
            These are the questions: \n\n{questions}\n\n. 
            Return from the set of questions random 1-8 unique ones, do not change them and do not add more questions when there is only one question only use that!

            
            Return only a JSON in the following format:

            {{
                "questions": [
                    "Question1",
                    "Question2",
                    "Question3",
                    "Question4",
                    "Question5",
                    "More Question"
                    ...
                ]
            }}

            Output the text in: \n\n{lang}\n\n
        """
        random_questions_json = self._generate_content(prompt)
        if "error" in random_questions_json:
            return {"error": "Failed to generate random questions"}
        return random_questions_json

    def weight_userPrefs(self, input_prefs):
        prompt = f"""
            You are tasked to evaluate a user's preferences based on the following JSON input: 

            {input_prefs}

            The user has made selections from various categories, with some preferences marked as 'chosen' and others as 'not chosen.' Your goal is to assign a weight (ranging from 0 to 100) to each category based on its significance. 

            Here are the key guidelines for your evaluation:

            1. **Weight Assignment**: Assign higher weights to categories that are 'chosen' and lower weights to those that are 'not chosen.'
            2. **Interconnectedness**: Consider the relationships between categories. For example, if the user selected 'Science' but did not choose 'Technology,' you should still assign a moderate weight to 'Technology' due to its inherent link to 'Science.'
            3. **Overall Context**: Analyze the entire set of preferences, ensuring that your weights reflect the user's interests holistically.

            Your response should be only a JSON and should look like this:

            {{
                "preferences": [
                    {{
                        "preference": "Technology",
                        "weight": 55
                    }},
                    {{
                        "preference": "Science",
                        "weight": 5
                    }},
                    {{
                        "preference": "Music",
                        "weight": 60
                    }}
                ]
            }}
        """
        userprefs = self._generate_content(prompt)
        return userprefs if "error" not in userprefs else "Error generating preferences"

    def evaluate_text(self, input_prefs, input_text):
        prompt = f"""
        I have the following list of tags: {input_prefs}. Your task is to assign 1 Main Tag and up to 3 Sub Tags to the following text:
                
        Text: {input_text}
        
        The Sub Tags can only be chosen from the list of tags, and Subtag one is more important than 3 or 2.        
        Return your response as JSON in the following format:

        {{
            "MainTag": {{
                "MainTag": "MainTagName"
            }},
            "SubTags": [
                {{
                    "SubTag1": "SubTagName1"
                }},
                {{
                    "SubTag2": "SubTagName2"
                }},
                {{
                    "SubTag3": "SubTagName3"
                }}
            ]
        }}
        """
        TagsHidden = self._generate_content(prompt)
        if "error" in TagsHidden:
            return {"error": "Failed to generate tags"}
        return TagsHidden

    def summarize_text(self, input_text, input_title, input_language):
        prompt = f"""
        I have the following text: {input_text}, with the title {input_title}. Your task is to strictly summarize this text in 1 sentence in the specified language {input_language}.

        -Do not interpret or add any additional information.
        -Be especially careful with names of individuals and companies.
        
        Return your response in JSON format as follows:
        {{"content_summary": "your summary goes here"}}
        """
        TagsHidden = self._generate_content(prompt)

        if "error" in TagsHidden:
            return {"success": False, "error": TagsHidden["error"]}

        return {"success": True, "content_summary": TagsHidden["content_summary"]}

    def extract_important_info(self, company_interests, input_text, jobs):
        logger.warning(f"Job: {company_interests}")
        prompt = f"""Your working at a company this is the profile of your company: {company_interests}. 
        Your job is to filter texts for really important details, like why a project failed or when the deadline is, new trends and categorize them. When there is important information in the text you should choose a job from this list {jobs} that relates
        with that information.
        So here’s your text:
        {input_text}

        -Do not interpret or add any additional information.
        -Be especially careful with names of individuals and companies.

        Return your response in JSON format as follows:
        {{ "job": "your summary goes here", 
        "importantInformation":[
            {{"info": "This project failed because of..."}},
            {{"info": "The deadline is in 2 weeks..."}},
            
        ] }}
        """
        extracted_info = self._generate_content(prompt)
        logger.warning(f"Extracted Info: {extracted_info}")
        return extracted_info

    def summarieze_tags(self, input_text, input_title, input_language, input_prefs):
        prompt = f"""
        I have the following text: {input_text}, with the title {input_title}. Your task is to strictly summarize this text in 1 sentence in the specified language {input_language}. Also give the text from the following list: {input_prefs} one main Tag and from 1 to 3 sub tags
        The Sub Tags can only be chosen from the list of tags, and Subtag one is more important than 3 or 2.        
        Return your response as JSON in the following format:

        {{
            "content_summary": "your summary goes here"
            "MainTag": {{
                "MainTag": "MainTagName"
            }},
            "SubTags": [
                {{
                    "SubTag1": "SubTagName1"
                }},
                {{
                    "SubTag2": "SubTagName2"
                }},
                {{
                    "SubTag3": "SubTagName3"
                }}
            ]
        }}"""

        summaryandtag = self._generate_content(prompt)
        logger.warning(f"Extracted Info: {summaryandtag}")
        return summaryandtag

    def _generate_MockResponse(self, moduleNumber):
        try:
            match moduleNumber:
                case 1:
                    return {
                        "module": "AI Module",
                        "questions": [
                            {
                                "question": "What is the purpose of AI?",
                                "answer": "To improve decision-making and problem-solving.",
                            }
                        ],
                    }
                case 2:
                    return {
                        "module": "ML Module",
                        "questions": [
                            {
                                "question": "What is the primary purpose of machine learning?",
                                "answer": "To create models that learn from data.",
                            }
                        ],
                    }
                case 3:
                    return {
                        """"Questions": [
                        "What event triggered the chain of diplomatic conflicts that led to the outbreak of World War I?",
                        "What were the main opposing alliances during World War I, and which countries were the key players in each alliance?",
                        "Describe the characteristics of trench warfare on the Western Front and name two significant battles that took place there.",
                        "What event led to Russia's exit from World War I, and what were the consequences for Russia?",
                        "How did the entry of the United States into World War I impact the course of the war?",
                        "What were some of the long-term consequences of World War I, particularly in terms of political upheaval and the treaty that officially ended the war?",
                        "Describe the characteristics of trench warfare on the Western Front and name two significant battles that took place there.",
                        "How did technological advancements, such as machine guns and artillery, influence the tactics and strategies used during World War I?",
                        "What role did propaganda play in shaping public opinion and support for the war effort during World War I?",
                        "Describe the impact of the Spanish flu pandemic on the course of World War I and its aftermath.",
                        "How did colonial territories and colonies contribute to the war effort of their respective empires during World War I?",
                        "Discuss the role of women in various capacities during World War I and how it impacted social norms and gender roles.",
                        "What were the economic consequences of World War I on Europe and the global economy?",
                        "Explain the concept of war reparations and their significance in the aftermath of World War I, particularly focusing on Germany.",
                        "How did the dissolution of the Ottoman Empire after World War I affect the geopolitical landscape of the Middle East?"
                        "Describe the characteristics of trench warfare on the Western Front and name two significant battles that took place there.",
                        "Describe the characteristics of trench warfare on the Western Front and name two significant battles that took place there.",
                        "Describe the characteristics of trench warfare on the Western Front and name two significant battles that took place there.",
                        "Describe the characteristics of trench warfare on the Western Front and name two significant battles that took place there.",
                        "]"""
                    }
                case 4:
                    return {
                        """
                            preferences": [
                            {"preference": "Technology", "chosen": True},
                            {"preference": "Science", "chosen": False},
                            {"preference": "Music", "chosen": False},
                            {"preference": "Culture and Art", "chosen": True},
                            {"preference": "Sports", "chosen": True},
                            {"preference": "Movies and Series", "chosen": True},
                            {"preference": "Education", "chosen": False},
                            {"preference": "Literature", "chosen": False},
                            {"preference": "History", "chosen": False},
                            {"preference": "Travel", "chosen": False},
                            {"preference": "Nature and Environment", "chosen": False},
                            {"preference": "Fashion", "chosen": False},
                            {"preference": "Culinary", "chosen": False},
                            {"preference": "Psychology", "chosen": False},
                            {"preference": "Finance", "chosen": True},
                            {"preference": "Space Exploration", "chosen": False},
                            {"preference": "Gaming", "chosen": False},
                            {"preference": "Creativity and Design", "chosen": False}
                        ]"""
                    }
                case _:
                    return {"error": "Invalid module number"}

        except Exception as e:
            print("Error")