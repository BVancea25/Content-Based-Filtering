from neo4j import GraphDatabase
from review_sentiment import Sentiment_Analyzer

class DB_UTILS:
   
    def __init__(self,uri,username,password):
        self.driver=GraphDatabase.driver(uri, auth=(username, password))
    
    def connect(self):
        self.session=self.driver.session()

    def close(self):
        self.driver.close()

    def create_node(self, label, properties):
        try:
            query = f"CREATE (n:{label} $props) RETURN n"
            result = self.session.run(query, props=properties)
            node = result.single()[0]
            return node
        except Exception as e:
            print(f"An error occurred while creating the node: {e}")
            return None
    
    def get_shoe(self, shoe_id):
        try:
            query = "MATCH (n:Item) WHERE id(n) = $node_id RETURN n"
            result = self.session.run(query, node_id=shoe_id)
            node = result.single()[0]
            properties = dict(node)
            del properties["profile"]
            return properties
        except Exception as e:
            print(f"An error occurred while getting the shoe: {e}")
            return None
    
    def delete_node(self, node_id):
        try:
            query = "MATCH (n) WHERE id(n) = $node_id DETACH DELETE n"
            self.session.run(query, node_id=node_id)
            return "Node deleted!"
        except Exception as e:
            print(f"An error occurred while deleting the node: {e}")
            return None
    
    def create_relationship(self, from_id, to_id, rel_type, properties={}):
        try:
            if(rel_type!="REVIEW"):
                query = "MATCH (from), (to) WHERE id(from) = $from_id AND id(to) = $to_id CREATE (from)-[rel:" + rel_type + "]->(to) SET rel += $properties RETURN rel"
                result = self.session.run(query, from_id=from_id, to_id=to_id, properties=properties)
                rel = result.single()[0]
                print("ceva")
                return rel
            else:
                query="MATCH (u:User) where id(u)=$from_id match (u)-[r:bought]->(i:Item) where id(i)=$to_id return r"
                result = self.session.run(query, from_id=from_id, to_id=to_id, properties=properties)
                result_list=list(result)
                if not result_list:
                    return "User didn't buy this item!!!"
                else:
                    properties=self.__useSentiment(properties)
                    query="MATCH (u:User) where id(u)=$from_id match (u)-[r:bought]->(i:Item) where id(i)=$to_id CREATE (u)-[new_r:REVIEW]->(i) SET new_r +=$properties DELETE r RETURN new_r"
                    result = self.session.run(query, from_id=from_id, to_id=to_id, properties=properties)
                    rel=result.single()[0]
                    return rel
        except Exception as e:
            print(f"An error occurred while creating the relationship: {e}")
            return None
    
    def __useSentiment(self,properties={}):
            analyzer=Sentiment_Analyzer(properties["text"])
            sentiment=analyzer.getSentiment()
            
            if sentiment=='Positive':
                    properties["rating"]+=2
            elif sentiment=='Negative':
                    properties["rating"]-=2

            if properties["rating"]>5:
                    properties["rating"]=5
            elif sentiment["rating"]<0:
                    properties["rating"]=1
            
            match properties["rating"]:
                case 1:
                    properties["weight"]=0.1
                case 2:
                    properties["weight"]=0.2
                case 4:
                    properties["weight"]=1.3
                case 5:
                    properties["weight"]=1.5
                
            return properties

    
   