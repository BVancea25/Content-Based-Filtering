from neo4j import GraphDatabase
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from numpy.linalg import norm
# Connect to the database
uri = "neo4j+s://e1957f84.databases.neo4j.io"
username = "neo4j"
password = "Sa_x8e3qWvizBrS_4DjXpjEu60bZkZ0Ga3Utaqmns04"
driver = GraphDatabase.driver(uri, auth=(username, password))
categories={
    "brand":["nike","adidas","Vans"],
    "color":["red","green","blue"],
    "type":["sneaker","boots","flip flops"]
}


def create_node(label, properties):
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        with driver.session() as session:
            query = f"CREATE (n:{label} $props) RETURN n"
            result = session.run(query, props=properties)
            node = result.single()[0]
            return node


def get_node(node_id):
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        with driver.session() as session:
            query = "MATCH (n) WHERE id(n) = $node_id RETURN n"
            result = session.run(query, node_id=node_id)
            node = result.single()[0]
            return node
        
def delete_node(node_id):
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        with driver.session() as session:
            query = "MATCH (n) WHERE id(n) = $node_id DETACH DELETE n"
            session.run(query, node_id=node_id)


def create_relationship(from_id, to_id, rel_type, properties={}):
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        with driver.session() as session:
            query = "MATCH (from), (to) WHERE id(from) = $from_id AND id(to) = $to_id CREATE (from)-[rel:" + rel_type + "]->(to) SET rel += $properties RETURN rel"
            result = session.run(query, from_id=from_id, to_id=to_id, properties=properties)
            rel = result.single()[0]
            return rel


def one_hot_encode_shoe_properties():
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        with driver.session() as session:
            query = "MATCH (n:Item) RETURN n.brand , n.type, n.color,id(n) as id"
            result = session.run(query)
            result_list=list(result)
            data=np.array([[node['n.brand'],node['n.type'],node['n.color']] for node in result_list])         
            ids=np.array([s["id"] for s in result_list])
           
            encoder=OneHotEncoder()
            encoded_data=encoder.fit_transform(data)
            array=encoded_data.toarray()
            for x in range(len(ids)):
                update_shoe_vector(ids[x],array[x])

            return ids,array
            
def update_shoe_vector(shoe_id, vector):
   
   with GraphDatabase.driver(uri, auth=(username, password)) as driver:
    
        query = """
            MATCH (n:Item)
            WHERE ID(n) = $shoe_id
            SET n.profile = $vector
            """
           
        with driver.session() as session:
            session.run(query, shoe_id=shoe_id, vector=vector)            
     
def build_user_profile(user_id):
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
    
        query = """
            MATCH (u:User)
            WHERE ID(u) = $user_id
            MATCH (u)-[r:SAW|bought]->(i:Item)
            RETURN i.profile,r.weight
            """
           
        with driver.session() as session:
            result=session.run(query, user_id=user_id)
            result_list=list(result)
            user_profile=[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
            for x in result_list: #am facut asta in cazul in care avem mai multe relatii nu doar SAW si bought
                if x["r.weight"]!=1:
                    for index,value in enumerate(x["i.profile"]):
                        if value !=0:
                            x["i.profile"][index]*=x["r.weight"]
                            user_profile[index]+=x["i.profile"][index]

            for i in range(len(user_profile)):
                if user_profile[i]!=0:
                    user_profile[i]/=len(result_list)
            
            query=""" 
                MATCH (u:User) WHERE ID(u)=$user_id
                SET u.profile=$user_profile
            """
            session.run(query,user_id=user_id,user_profile=user_profile)
            
def best_recommendation(user_id):
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
    
        query = """
            MATCH (u:User)
            WHERE id(u) = 0
            MATCH (i:Item)
            WHERE NOT EXISTS((u)-[:SAW|bought]->(i))
            RETURN u.profile AS user_profile, COLLECT(i.profile) AS item_profiles, COLLECT(id(i)) AS ids
            """
           
        with driver.session() as session:
            result=session.run(query,user_id=user_id)
            result_list=list(result)

            user_profile=np.array(result_list[0][0])
            item_profiles=np.array(result_list[0][1])
           
            cos_sim=np.dot(item_profiles,user_profile)/(norm(item_profiles,axis=1)*norm(user_profile))
            return get_node(result_list[0][2][np.argmax(cos_sim)])




print(best_recommendation(0))
