
from constants import dt,G

class Vector:
    def __init__(self,xi,yi,xf,yf):
        self.x = xf-xi
        self.y = yf-yi
        self.magintude = ((xf-xi)**2 + (yf-yi)**2)**0.5

    def normalize(self):
        return Vector(0,0,self.x/self.magintude,self.y/self.magintude)
    
    def multiply_scalar(self,k):
        self.x = self.x *k
        self.y = self.y*k
        return self

class Body:
    def __init__(self,mass,x,y,vx,vy):
        self.mass = mass
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.trail = []

    def update(self,other):
        accel = self.acceleration(other)
        
        self.vx += accel.x*dt
        self.vy += accel.y*dt
        self.x += self.vx*dt
        self.y +=self.vy*dt
        print(self.vx,self.vy,accel.x,accel.y)
        
    def acceleration(self,other):
        # consider we will use earth as self and sun as other
        radius = ((self.x-other.x)**2 + (self.y-other.y)**2)**0.5
        #print(radius)
        ForceMag  = (G*other.mass)/((radius)**2)
        ForceVec = Vector(self.x,self.y,other.x,other.y)
        ForceVecNorm = ForceVec.normalize()
        Forcefinal = ForceVecNorm.multiply_scalar(ForceMag)
        return Forcefinal # this is the vector with the scalar factor multiplied
    
        
