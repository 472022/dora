import google.generativeai as genai

genai.configure(api_key="AIzaSyBU_x0c0bpr4YscssxOBcxBMqb010aHZwI")

model = genai.GenerativeModel("gemini-1.5-pro")
response = model.generate_content("What is AI?")
print(response.text)
