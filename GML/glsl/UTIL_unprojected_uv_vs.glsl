#version 330

in vec4 in_coordinate;

out vec2 vs_uv;

void main(){
  gl_Position = vec4(in_coordinate.xy, 0.0, 1.0);
  vs_uv = in_coordinate.zw;
}
