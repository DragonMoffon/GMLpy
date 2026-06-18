#version 430
/*
   For inverse ray shooting (IRS) lens magnification the lens positions are stored relative to the center of mass.
   all positions in einstein angles.
*/

struct Lens {
  float mass; // Mass in Solar Masses
  float einstein_sqr; // einstein angle of the lens (Squared to save on duplicate calculations)
  vec2 position; // position in einstein angle of the whole lens system
};

layout(std430) readonly buffer lensBlock {
  int count;
  int reserved;
  Lens lens[];
} lenses;

vec2 find_deflection(vec2 ray, vec2 lens, float radius_sqr){
  vec2 relative = ray - lens;
  // we don't need the sqrt because we need to normalise relative and also divide by separation which is sqrt * sqrt.
  float separation = dot(relative, relative);
  return radius_sqr * relative / separation;
}

in vec2 vs_uv; // (x, y) location in lens place

out vec4 fs_ray; // (r, g) location in source plane, (b) reserved, (a) 1.0;

void main(){
  vec2 fs_pos = vs_uv;
  for (int i = 0; i < lenses.count; i++){
    fs_pos = fs_pos - find_deflection(vs_uv, lenses.lens[i].position, lenses.lens[i].einstein_sqr);
  }

  fs_ray = vec4(fs_pos, 0.0, 1.0);
}
