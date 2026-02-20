from google import genai

client = genai.Client(api_key="AIzaSyCnufRsLH5E8MyAqEgxu9ogp-DiinyOskQ")

for m in client.models.list():
    print(f"ID: {m.name} | Display Name: {m.display_name}")