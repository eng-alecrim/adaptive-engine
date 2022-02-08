##Author: Ilia Rushkin, VPAL Research, Harvard University, Cambridge, MA, USA

##This function maps the user_id to the user index used by other functions, and also adds new users
##SYNCHRONIZATION IS IMPORTANT
def mapUser(user_id):
    
    global users
    
    try:
        u=np.where(users==user_id)[0][0]
    except:
        global n_users, last_seen, m_L, m_exposure, m_unseen, m_correctness, m_timestamp
        u=n_users
        n_users+=1
        users=np.append(users,user_id)
        last_seen=np.append(last_seen,-1)
        m_L=np.vstack((m_L,L_i))
        m_exposure=np.vstack((m_exposure,row_exposure))
        m_unseen=np.vstack((m_unseen,row_unseen))
        m_correctness=np.vstack((m_correctness,row_correctness))
        m_timestamp=np.vstack((m_timestamp,row_timestamp))
        
    
    return u


def mapItem(item_id):
    
    global items
    
    item=np.where(items==item_id)[0][0]
        
    return(item)

def bayesUpdate(u, item, score=1, time=0):
  
  
  #This function updates the user mastery and record of interactions that will be needed for recommendation and estimation of the BKT
  
  # global m_x0_add, m_k, m_L, m_trans, last_seen, m_unseen, m_correctness, m_timestamp, m_exposure, m_tagging, log_epsilon
  
  
  last_seen[u]=item
  self.m_correctness[u,item]=score
  self.m_timestamp[u,item]=time
  if m_unseen[u,item]:
      self.m_unseen[u,item]=False
      self.m_exposure[u,]+=self.m_tagging[item,]
  
  ##The increment of log-odds due to evidence of the problem, but before the transfer
  x=self.m_x0_add[item,]+score*self.m_k[item,]
  L=self.m_L[u,]+x
  
  ##Add the transferred knowledge
  trans=self.m_trans[item,]
  #L=np.log(trans+(trans+1)*np.exp(L))
  L=np.log(trans+(trans+1)*np.exp(L))
  
  L[np.isposinf(L)]=self.log_epsilon
  L[np.isneginf(L)]=-self.log_epsilon
  
  self.m_L[u,]=L
  #return{'L':L, 'x':x}
  



#This function calculates the probability of correctness on a problem, as a prediction based on student's current mastery.
def predictCorrectness(u, item):
    
    global m_L, m_p_slip, m_p_guess
    
    L=m_L[u,]
    p_slip=m_p_slip[item,];
    p_guess=m_p_guess[item,];
    
    odds=np.exp(L);
  
    x=(odds*(1.0-p_slip)+p_guess)/(odds*p_slip+1.0-p_guess); ##Odds by LO
    x=np.prod(x) ##Total odds
  
    p=x/(1+x) ##Convert odds to probability
    if np.isnan(p) or np.isinf(p):
          p=1.0
  
    return(p)



##This function returns the id of the next recommended problem. If none is recommended (list of problems exhausted or the user has reached mastery) it returns None.
def recommend(u, module=1, stopOnMastery=True):
    
    global m_L, L_star, m_w, m_unseen, m_k, r_star, last_seen, m_difficulty_add, V_r, V_d, V_a, V_c, scope
            
    #Subset to the unseen problems and calculate problem readiness and demand
    ind_unseen=np.where(m_unseen[u,] & (scope==module)|(scope==0))[0]

    N=len(ind_unseen)
    
    if(N==0): ##This means we ran out of problems, so we stop
        next_item = None
        
    else:
        L=m_L[u,]
        
        #Calculate the user readiness for LOs
        
        m_r=np.dot(np.minimum(L-L_star,0), m_w);
        m_k_unseen=m_k[ind_unseen,]
        R=np.dot(m_k_unseen, np.minimum((m_r+r_star),0))
        D=np.dot(m_k_unseen, np.maximum((L_star-L),0))
        
        if last_seen[u]<0:
            C=np.repeat(0.0,N)
        else:
            C=np.dot(m_k_unseen, m_k[last_seen[u],])
            
        #A=0.0
        d_temp=m_difficulty_add[:,ind_unseen]
        L_temp=np.tile(L,(N,1)).transpose()
        A=-np.diag(np.dot(m_k_unseen,np.abs(L_temp-d_temp)))
        
        if stopOnMastery and sum(D)==0: ##This means the user has reached threshold mastery in all LOs relevant to the problems in the homework, so we stop
            next_item=None
        else:
            
            temp=(A.max()-A.min());
            if(temp!=0.0):
                A=A/temp
            
            temp=(D.max()-D.min());
            if(temp!=0.0):
                D=D/temp
                            
            temp=(R.max()-R.min());
            if(temp!=0.0):
                R=R/temp
            
            temp=(C.max()-C.min());
            if(temp!=0.0):
                C=C/temp     
            
            next_item=ind_unseen[np.argmax(V_r*R+V_d*D+V_a*A+V_c*C)]
            
    
    return(next_item)

    

#This function updates the BKT model using the estimates from student data.
def updateModel():
    
    global eta, M, L_i, m_exposure, m_L, m_L_i, m_trans, m_guess, m_slip
    est=estimate(eta, M)

    L_i=np.log(est['L_i'])
    m_L_i=np.tile(L_i,(m_L.shape[0],1))
    
    ind_pristine=np.where(m_exposure==0.0)
    m_L[ind_pristine]=m_L_i[ind_pristine]
    m_trans=1.0*est['trans']
    m_guess=1.0*est['guess']
    m_slip=1.0*est['slip']
