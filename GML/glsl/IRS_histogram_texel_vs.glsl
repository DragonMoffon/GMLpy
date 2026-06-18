#version 330


uniform sampler2D deflection_map;

in ivec2 origin;
out vec2 vs_uv;

void main(){
    // For high resolution deflection maps it is not worth it to sample interpolated
    // values. This also makes the IRS deterministic rather than random
    vec2 target = texelFetch(deflection_map, origin, 0).rg * 0.5;
    gl_Position = vec4(target, 0.0, 1.0);
}
