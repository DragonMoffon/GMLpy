#version 330

uniform sampler2D texture0;

uniform vec4 source;

in vec2 vs_uv;
out vec4 fs_colour;

void main(){
  vec2 loc = vs_uv * 6.0 - 3.0;
  vec2 pos = texture(texture0, vs_uv).xy;

  fs_colour = vec4(0.0, 0.0, 1.0 - step(source.z, length(loc - source.xy)), 1.0);
  fs_colour += vec4(vec3(1.0 - step(source.z, length(pos - source.xy))), 1.0);
}
