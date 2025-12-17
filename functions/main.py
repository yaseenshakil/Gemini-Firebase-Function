# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app
import json, os
from google import genai

# For cost control, you can set the maximum number of containers that can be
# running at the same time. This helps mitigate the impact of unexpected
# traffic spikes by instead downgrading performance. This limit is a per-function
# limit. You can override the limit for each function using the max_instances
# parameter in the decorator, e.g. @https_fn.on_request(max_instances=5).
set_global_options(max_instances=10)
PROMPT = """Generate {no_of_questions} multiple choice questions about {topic}.
    Return the result strictly as a JSON array of objects.
    Each object must use the following structure:
    {{
      'question': 'string',
      'choices': ['A', 'B', 'C', 'D'],
      'correct_answer': 'string'
      }}
      Do NOT include explanations, prose, or anything outside the JSON.
      Do NOT include letter demarkation in the possible choices.
      Do NOT include letter demarkation in the correct_answer.
      Return ONLY valid JSON."""
    


@https_fn.on_request()
def on_request_api_key(req: https_fn.Request) -> https_fn.Response:
    try:
        # CORS preflight request handling for browsers
        if req.method == "OPTIONS":
            return https_fn.Response(
            "",
            status=204,
            headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
            },
        )
        topic = req.args.get('topic')
        no_of_questions = int(req.args.get('no_of_questions', "5"))
        no_of_questions = 5 if no_of_questions not in [5,10] else no_of_questions
        if not topic or not no_of_questions:
            return https_fn.Response(json.dumps({"error":"No topic or no_of_questions parameters provided"})
                                     , status=400,
                                     headers={"Content-Type": "application/json", 
                                              "Access-Control-Allow-Origin": "*"})
        prompt_formatted = PROMPT.format(topic=topic, no_of_questions=no_of_questions)
        client = genai.Client(api_key="SECRET_API_KEY")
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=f"{prompt_formatted}"
        )
        raw = response.text.strip()

        # Remove markdown code fences if present
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.replace("json", "", 1).strip()

        if not raw:
            raise ValueError("Model returned empty response")

        parsed_response = json.loads(raw)
        
        return https_fn.Response(
            json.dumps(parsed_response)
            ,headers={
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
                }, status=200)
    except Exception as e:
        return https_fn.Response(
            json.dumps({"internal_error": str(e)}),
            status=500,
            headers={"Access-Control-Allow-Origin": "*"},
        )