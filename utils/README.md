# Psychopy-pixx utils

In our lab, we use some additional scripts and configurations to
use psychopy.

## Switching between psychopy and psychtoolbox

In our lab we use psychopy and psychtoolbox (PTB) on one computer,
however both setups require some orthogonal configurations, especially to handle
multiple monitors. 

While psychopy-pixx require a running VPixx system service, this service conflicts with PTB. 
In addition, psychopy expects multiple monitors as one big virtual one (the Linux default), while
PTB uses Zaphodheads and a custom Xorg configuration (PTB command `XorgVConfCreator`). 

Our lab users run helper scripts `set-psychopy-mode` and `set-ptb-mode` to automate these configurations. 
Changes in the Xorg config require a logout/login. 
An additional sudoer configuration allows to start/stop the system service without administrator rights (see `sudoers-ptb-psychopy` file, users are in a *psychtoolbox* group).

