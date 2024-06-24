/* ray tracing shader core code */

#version 330 core
precision highp float;

// constants
#define MAXDEPTH 	5
#define NUMSAMPLES 	4
#define MAXFLOAT	99999.99

const float PI = 3.14159265359;

// varyings
in vec2 coords_v; 
in vec3 position;
out vec4 FragColor;

// camera uniforms
uniform vec3 camera_offset;
uniform vec3 camera_position;

// mobjects uniforms


// structures
struct Ray{
    vec3 origin;
    vec3 direction;
};

struct Sphere{
    vec3 center;
    float radius;

    int   materialType;
    vec3  albedo;
    float fuzz;
    float refractionIndex;
};

struct IntersectInfo{
    // surface properties
    float t;
    vec3  p;
    vec3  normal;
	
    // material properties
    int   materialType;
    vec3  albedo;
    float fuzz;
    float refractionIndex;
};

Sphere sphere1 = Sphere(vec3(2.0, 0.0, 0.0), 1.0, 0, vec3( 0.5, 0.5, 0.5), 1.0, 1.0);
Sphere sphere2 = Sphere(vec3(0.0, 0.0, 0.0), 1.0, 0, vec3( 0.5, 0.5, 0.5), 1.0, 1.0);
Sphere sphere3 = Sphere(vec3(0.0, 0.0, -11.000000000), 10.000000000, 0, vec3( 0.5, 0.5, 0.5), 1.0, 1.0);

// functions
bool Sphere_hit(Sphere sphere, Ray ray, float t_min, float t_max, out IntersectInfo rec){
    vec3 oc = ray.origin - sphere.center;
    float a = dot(ray.direction, ray.direction);
    float b = dot(oc, ray.direction);
    float c = dot(oc, oc) - sphere.radius * sphere.radius;

    float discriminant = b * b - a * c;

    if (discriminant > 0.0f)
    {
        float temp = (-b - sqrt(discriminant)) / a;

        if (temp < t_max && temp > t_min)
        {
            rec.t                = temp;
            rec.p                = ray.origin + rec.t * ray.direction;
            rec.normal           = (rec.p - sphere.center) / sphere.radius;
            rec.materialType     = sphere.materialType;
            rec.albedo           = sphere.albedo;
            rec.fuzz             = sphere.fuzz;
            rec.refractionIndex  = sphere.refractionIndex;

            return true;
        }


        temp = (-b + sqrt(discriminant)) / a;

        if (temp < t_max && temp > t_min)
        {
            rec.t                = temp;
            rec.p                = ray.origin + rec.t * ray.direction;
            rec.normal           = (rec.p - sphere.center) / sphere.radius;
            rec.materialType     = sphere.materialType;
            rec.albedo           = sphere.albedo;
            rec.fuzz             = sphere.fuzz;
            rec.refractionIndex  = sphere.refractionIndex;

            return true;
        }
    }

    return false;
}

vec3 get_background_color(){
    vec2 coords = coords_v;
    int grid_x = int((coords.x + 1.) * 10.);
    int grid_y = int((coords.y + 1.) * 10.);
    
    bool is_black_tile = (grid_x ^ grid_y) % 2 == 1;
    
    return is_black_tile ? vec3(0.5, 0.5, 0.8) : vec3(0.6, 0.6, 1.0);
}

vec3 rayTrace(Ray ray, int depth){ 
    IntersectInfo intersectData;
    if(Sphere_hit(sphere1, ray, 0.001, MAXFLOAT, intersectData))
        return vec3(1.0, 0.0, 0.0);
    else if(Sphere_hit(sphere2, ray, 0.001, MAXFLOAT, intersectData))
        return vec3(0.0, 1.0, 0.0);
    // else if(Sphere_hit(sphere3, ray, 0.001, MAXFLOAT, intersectData))
    //     return vec3(0.0, 0.0, 1.0);
    else
        return get_background_color();
}

void main(){
    // get the initial ray from the camera
    Ray cameraRay;
    cameraRay.origin = camera_position;
    cameraRay.direction = normalize(position - camera_position);// TODO, neccesary to normalize?
    
    FragColor = vec4(rayTrace(cameraRay, 0), 1.0); // depth currently not in use
}