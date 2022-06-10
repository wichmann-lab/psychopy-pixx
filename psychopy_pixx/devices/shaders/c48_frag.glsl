 /* C48 output formatter
 *
 * Converts from a 16bit framebuffer object into a 8bit per channel frame
 * for use in ViewPixx devices with C48 mode (16 bit per color channel)
 * 
 * Shader is based on the color++ shader in psychopy.
 * Some of the ideas go back to Mario Kleiner and psychtoolbox.
 */
    uniform sampler2D fbo;
    uniform sampler2D clut;
    uniform bool gamma_correction_flag;
    vec3 index;
    vec2 coords;

    void main() {
        vec4 fboFrag = texture2D(fbo, gl_TexCoord[0].st);
        index = fboFrag.rgb * 65535.0;
        if (gamma_correction_flag) {
            for (int i=0; i < 3; i++) {
                /* texture coords range 0..1
                 * Pixels range [0-1/255, 1/255-2/255, ..., 254/255-1]
                 * => add 0.5 to indices to lookup pixel values */
                coords = (vec2(mod(index[i], 256.0), floor(index[i] / 256.0)) + 0.5) / 256.0;
                index[i] = texture2D(clut, coords)[i] * 65535.0;
            }
        }
        index = floor(index + 0.5) + 0.01;
        if (mod(gl_FragCoord.x, 2.0) < 1.0){
            gl_FragColor.rgb = floor(index / 256.0) / 255.0;
        }
        else {
            /* Odd output pixel: */
            gl_FragColor.rgb = mod(index, 256.0) / 255.0;
            /* Ensure alpha channel to 1.0. */
            gl_FragColor.a = 1.0;
        }
    }
