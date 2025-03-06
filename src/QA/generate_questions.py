import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env")

def generate_questions(transcription_text: str, module: str) -> None:
    """
    Generate questions from the given transcription text and module name.

    Parameters:
        transcription_text (str): The full transcription text of the video.
        module (str): The module or course name associated with the video.

    Returns:
        None
    """
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Prompt for MCQ generation
        prompt = f"""You are an expert question generator. I will provide you with a transcript of content,
and your task is to create multiple multiple-choice questions (MCQs) that test the viewer's understanding
of the key topics discussed in the transcript. Each question should be on-topic, focusing on the main ideas and important details,
rather than personal anecdotes or peripheral issues. The questions should focus on the content and concepts, and should not include any personal names or references.

Instructions:
1. Analyze the provided transcript carefully and identify several key topics or concepts.
2. For each identified topic, generate one multiple-choice question (MCQ) that reflects the essence of the content.
3. Each MCQ should include exactly four options for answers, where one option is correct and the other three are plausible distractors.
4. Do not include any additional commentary, explanations, or text outside of the required JSON output.
5. The JSON output must follow this exact format:
[
    {{
        "q": "Your generated question text goes here.",
        "options": [
            "Option 1",
            "Option 2",
            "Option 3",
            "Option 4"
        ]
    }},
    ... (more question objects as needed)
]
6. Do not output any extra keys or fields; each object must only include "q" and "options".
7. Ensure that the JSON is properly formatted and only covers topics mentioned in the transcript.
8. In particular, avoid mentioning any names and instead refer generically to the subject matter.

Module: {module}
Transcript: {transcription_text}

Based on the transcript above, please generate multiple MCQs as specified."""

        # Generate questions using the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "developer", 
                    "content": "You are an expert MCQ generator. Provide the MCQ in the exact JSON format as instructed."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "mcqs_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "mcqs": {
                                "description": "List of generated MCQs",
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "q": {
                                            "description": "The generated question",
                                            "type": "string"
                                        },
                                        "options": {
                                            "description": "The four multiple-choice options",
                                            "type": "array",
                                            "minItems": 4,
                                            "maxItems": 4,
                                            "items": {
                                                "type": "string"
                                            }
                                        }
                                    },
                                    "required": ["q", "options"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["mcqs"],
                        "additionalProperties": False
                    }
                }
            }
        )
        output_dir = os.path.join("..", "..", "data", "mcq")
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, f"{module}.json")

        mcq_json = response.choices[0].message.content
        with open(output_filename, "w") as f:
            f.write(mcq_json)
        print(f"MCQ saved to {output_filename}")
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return








