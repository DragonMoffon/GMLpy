#version 420

uniform sampler2D texture0;
layout(binding = 1) uniform sampler2D texture1;

uniform float ray_count; 

in vec2 vs_uv;
out vec4 fs_colour;

void main(){
  fs_colour = vec4(texture(texture0, vs_uv).rrr/ray_count, 1.0);
  // fs_colour = vec4(texture(texture0, vs_uv).r/ray_count, texture(texture1, vs_uv).rg * 0.5 + 0.5, 1.0);
}
