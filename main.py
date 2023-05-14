from recommendation_engine import Engine
from dotenv import load_dotenv
import os

load_dotenv()
uri=os.getenv('NEO4J_URI')
user=os.getenv('NEO4J_USER')
password=os.getenv('NEO4J_PASS')

handler=Engine(uri,user,password)
handler.connect()
#handler.build_user_profile(0)
#handler.build_user_profile(2)
#print(handler.create_relationship(0,5,"REVIEW",{"ceva":"blabla"}))
#handler.create_relationship(0,5,"REVIEW",{"text":"I like this product alot","rating":4,"weight":1})
#handler.one_hot_encode_shoe_properties()
handler.close()