/* M16 output formatter
 *
 * Converts from a 16bit framebuffer object into a 8bit per channel frame
 * for use in ViewPixx devices with M16 mode (16-bit luminance mode)
 * 
 * Shader is based on the bits++ shader in psychopy.
 * Some of the ideas go back to Mario Kleiner and psychtoolbox.
 */
    uniform sampler2D fbo;
    uniform sampler2D clut;
    uniform bool gamma_correction_flag;
    float color;
    vec2 coords;
    
    void main() {
        vec4 fboFrag = texture2D(fbo, gl_TexCoord[0].st);
        color = fboFrag.r * 65535.0;
        if (gamma_correction_flag) {
            /* texture coords range 0..1
               Pixels range [0-1/255, 1/255-2/255, ..., 254/255-1]
               => add 0.5 to indices to lookup pixel values */
            coords = (vec2(mod(color, 256.0), floor(color / 256.0)) + 0.5) / 256.0;
            color = texture2D(clut, coords).a * 65535.0;
        }
        color = color + 0.01;  // avoid rounding issues, idea by Mario Kleiner (psychtoolbox)
        gl_FragColor.rgb = vec3(floor(color / 256.0), mod(color, 256.0), 0) / 255.0;
    } 
