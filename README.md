# Computing Currency Devaluation Events

Using World Bank annual data for LCU:USD *X_i* exchange rates and local consumption price indices *P_i*, I am calculating devalation events in *R_i=X_i/P_i*

## Open issues

- initial and terminal point problems
    - in Cameroon, Cape Verde, ethiopia, gambia, guinea, mauritania, morocco, mozambique, namibia, nigeria, rwanda, ZAF
- internal non-intersection of baseline *B_i* with *R_i* 
    - Eswatini, Botswana, Burkina Faso, ghana, malawi, namibia, ZAF
- overlapping events in 
    - egypt, eritrea, lesotho
- event not being picked up 
    - somalia
- wrong initial date
    - zambia
- something is wrong in chad
    - i am only looking at the next peak after the ma trough. i might have to look at all peaks or at the higher peak

