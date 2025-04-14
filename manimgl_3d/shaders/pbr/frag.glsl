#version 330 core

const float PI = 3.14159265359;

#define MAX_LIGHTS 16

// From Vertex Shader
in vec3 WorldPos;
in vec3 Normal;
in vec3 Tangent;
in vec2 tex_coords_v;

// From Camera
uniform vec3 light_positions[MAX_LIGHTS];
uniform vec3 light_source_position;         // NOT USED, left for compatibility with non-PBR mobjects
uniform vec3 light_colors[MAX_LIGHTS];
uniform int light_count;
uniform vec3 camera_position;
uniform float bloom_threshold;

// PBR textures (from SurfacePBR.material -> shaderwrapper -> PBRCamera)
uniform sampler2D tex_albedo;
uniform sampler2D tex_roughness;
uniform sampler2D tex_metallic;
uniform sampler2D tex_ao;
uniform sampler2D tex_normal;


layout (location = 0) out vec4 FragColor; // render into hdr_color_buffer
layout (location = 1) out vec4 BrightColor; // render into hdr_bright_buffer

float DistributionGGX(vec3 N, vec3 H, float roughness)
{
    float a = roughness*roughness;
    float a2 = a*a;
    float NdotH = max(dot(N, H), 0.0);
    float NdotH2 = NdotH*NdotH;

    float nom   = a2;
    float denom = (NdotH2 * (a2 - 1.0) + 1.0);
    denom = PI * denom * denom;

    return nom / denom;
}

float GeometrySchlickGGX(float NdotV, float roughness)
{
    float r = (roughness + 1.0);
    float k = (r*r) / 8.0;

    float nom   = NdotV;
    float denom = NdotV * (1.0 - k) + k;

    return nom / denom;
}

float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness)
{
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float ggx2 = GeometrySchlickGGX(NdotV, roughness);
    float ggx1 = GeometrySchlickGGX(NdotL, roughness);

    return ggx1 * ggx2;
}

vec3 fresnelSchlick(float cosTheta, vec3 F0)
{
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

vec3 getNewNormal(vec3 mapNormal)
{
    vec3 Bitangent = cross(Tangent, Normal);
    mat3 tbn = mat3(Tangent, Bitangent, Normal);
    return normalize(tbn * mapNormal);
}

void main()
{
    vec3 albedo = pow(texture(tex_albedo, tex_coords_v).rgb, vec3(2.2)); // from sRGB to linear space
    float roughness = texture(tex_roughness, tex_coords_v).r;
    float metallic = texture(tex_metallic, tex_coords_v).r;
    float ao = texture(tex_ao, tex_coords_v).r;
    vec3 map_normal = texture(tex_normal, tex_coords_v).rgb * 2.0 - 1.0;

    vec3 N = getNewNormal(map_normal);
    vec3 V = normalize(camera_position - WorldPos);

    vec3 F0 = vec3(0.04);                      // for dia-electric (like plastic)
    F0 = mix(F0, albedo, metallic);            // for metal

    // reflectance equation
    vec3 Lo = vec3(0.0);

    for (int i = 0; i < light_count; i++)
    {
        // calculate per-light radiance
        vec3 L = normalize(light_positions[i] - WorldPos);
        vec3 H = normalize(V + L);
        float distance = length(light_positions[i] - WorldPos);
        float attenuation = 1.0 / (distance * distance);
        vec3 radiance = light_colors[i] * attenuation;

        // Cook-Torrance BRDF
        float NDF = DistributionGGX(N, H, roughness);   
        float G   = GeometrySmith(N, V, L, roughness);      
        vec3 F    = fresnelSchlick(clamp(dot(H, V), 0.0, 1.0), F0);
           
        vec3 numerator    = NDF * G * F; 
        float denominator = 4.0 * max(dot(N, V), 0.0) * max(dot(N, L), 0.0) + 0.0001; // + 0.0001 to prevent divide by zero
        vec3 specular = numerator / denominator;
        
        // kS is equal to Fresnel
        vec3 kS = F;
        // for energy conservation, the diffuse and specular light can't
        // be above 1.0 (unless the surface emits light); to preserve this
        // relationship the diffuse component (kD) should equal 1.0 - kS.
        vec3 kD = vec3(1.0) - kS;
        // multiply kD by the inverse metalness such that only non-metals 
        // have diffuse lighting, or a linear blend if partly metal (pure metals
        // have no diffuse light).
        kD *= 1.0 - metallic;	  

        // scale light by NdotL
        float NdotL = max(dot(N, L), 0.0);        

        // add to outgoing radiance Lo
        Lo += (kD * albedo / PI + specular) * radiance * NdotL;  // note that we already multiplied the BRDF by the Fresnel (kS) so we won't multiply by kS again
    }

    // ambient lighting (note that the next IBL tutorial will replace 
    // this ambient lighting with environment lighting).
    vec3 ambient = vec3(0.03) * albedo * ao;

    vec3 color = ambient + Lo;

    FragColor = vec4(color, 1.0); //

    bool exceed_brightness = dot(color, vec3(0.2126, 0.7152, 0.0722)) > bloom_threshold;
    if (exceed_brightness){
        BrightColor = FragColor;
    } else {
        BrightColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
}