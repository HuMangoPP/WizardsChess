#version 330 core
#define KERNEL_SIZE 5

layout (location = 0) out vec4 fragColor;

in vec2 uvs;
in vec2 screen_res;

uniform sampler2D tex;
uniform float weight[KERNEL_SIZE] = float[] (0.3829,	0.2417,	0.0606,	0.0060,	0.0002);

void main() {
    vec2 st = gl_FragCoord.xy/screen_res;

    vec2 tex_offset = 2.0 / textureSize(tex, 0);
    vec4 color = vec4(st.x, 0.0, st.y, 1.0) * vec4(texture(tex, uvs).rgba) * weight[0];
    // horizontal
    for (int i = 1; i < KERNEL_SIZE; i++) {
        color += vec4(texture(tex, uvs + vec2(tex_offset.x * i, 0.0)).rgba) * weight[i];
        color += vec4(texture(tex, uvs - vec2(tex_offset.x * i, 0.0)).rgba) * weight[i];
    }
    // vertical
    for (int i = 1; i < KERNEL_SIZE; i++) {
        color += vec4(texture(tex, uvs + vec2(0.0, tex_offset.y * i)).rgba) * weight[i];
        color += vec4(texture(tex, uvs - vec2(0.0, tex_offset.y * i)).rgba) * weight[i];
    }

    fragColor = vec4(color.rgb, color.r + color.g + color.b);
}