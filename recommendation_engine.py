from db_utils import DB_UTILS
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from numpy.linalg import norm


class Engine(DB_UTILS):

    def __init__(self, uri, username, password):
        super().__init__(uri, username, password)

    def update_shoe_vector(self, shoe_id, vector):
        try:
            query = """
                MATCH (n:Item)
                WHERE ID(n) = $shoe_id
                SET n.profile = $vector
            """              
            self.session.run(query, shoe_id=shoe_id, vector=vector)
            return "Vector updated!"
        except Exception as e:
            # Log the error message or handle the exception as appropriate for your application
            print(f"An error occurred while updating the shoe vector: {str(e)}")
            return None    


    def one_hot_encode_shoe_properties(self):
        try:
            query = "MATCH (n:Item) RETURN n.brand , n.type, n.color,id(n) as id"
            result = self.session.run(query)
            result_list=list(result)
            data=np.array([[node['n.brand'],node['n.type'],node['n.color']] for node in result_list])  
            ids=np.array([s["id"] for s in result_list])
            
            encoder=OneHotEncoder()
            encoded_data=encoder.fit_transform(data)
            array=encoded_data.toarray()
            for x in range(len(ids)):
                self.update_shoe_vector(ids[x],array[x]) #inseram vectorii in baza de date

            return ids,array
        except Exception as e:
            print(f"An error occurred while updating the shoe vector:{str(e)}")
            return None
    
        #construim profilul userului cu ajutorul profilelor papucilor cu care a interactionat acesta     
    def build_user_profile(self,user_id):
            try: 
                #returneaza vectorii papucilor alaturi de weightul relatiei
                query = """ 
                    MATCH (u:User)
                    WHERE ID(u) = $user_id
                    MATCH (u)-[r:SAW|bought|REVIEW]->(i:Item)
                    RETURN i.profile,r.weight
                    """
                result=self.session.run(query, user_id=user_id)
                result_list=list(result)
                user_profile=[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]

                for x in result_list:      #am facut asta in cazul in care avem mai multe relatii nu doar SAW si bought
                    if x["r.weight"]!=1:    
                        for index,value in enumerate(x["i.profile"]):#inmultim vectorul cu weightul corespunzator
                            if value !=0:
                                x["i.profile"][index]*=x["r.weight"]
                                user_profile[index]+=x["i.profile"][index]#adunam valorile tuturor vectorilor

                for i in range(len(user_profile)):#impartim rezultatul la numarul papucilor
                    if user_profile[i]!=0:
                        user_profile[i]/=len(result_list)   
                print(user_profile)
                query=""" 
                    MATCH (u:User) WHERE ID(u)=$user_id
                    SET u.profile=$user_profile
                """
                self.session.run(query,user_id=user_id,user_profile=user_profile)
            except Exception as e:
                print(f"Error while calculating user profile:{str(e)}")
                return None
        
    def best_recommendation(self,user_id):
    
        try:
        #returneaza profilul userului target, profilul tuturor papucilor cu care acesta nu a interactionat si idurile acestora
            query = """
                MATCH (u:User)
                WHERE id(u) = $user_id
                MATCH (i:Item)
                WHERE NOT EXISTS((u)-[:SAW|bought]->(i))
                RETURN u.profile AS user_profile, COLLECT(i.profile) AS item_profiles, COLLECT(id(i)) AS ids
                """
            result=self.session.run(query,user_id=user_id)
            result_list=list(result)
            
            user_profile=np.array(result_list[0][0])
            item_profiles=np.array(result_list[0][1])
            
            cos_sim=np.dot(item_profiles,user_profile)/(norm(item_profiles,axis=1)*norm(user_profile))#calculam similaritatea cosinus
            
            return self.get_shoe(result_list[0][2][np.argmax(cos_sim)])#returnam papucul cu similaritatea cea mai mare
        except Exception as e:
            print(f"Error occured while retreiving recommendation:{str(e)}")
            return None
    
    