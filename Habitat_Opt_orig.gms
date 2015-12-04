$title Barrier Removal and Lampricide Applicaiton (Fishworks v5)

* DEFINE COMMAND-LINE OPTIONS

* input gdx
$if not set inputfile $set inputfile 'data.gdx'


* SETS AND DEFINITIONS

sets
    Fishes(*) 'set of target species for restoration or control (by species identity)',
    Barriers(*) 'set of candidate dams/road culverts for removal/upgrade (by ID number)';
alias
    (Fishes,F),
    (Barriers,J,K);
sets
    Downstream(J,K) 'K is the barrier immediately downstream from J; used for tracing upstream/downstream effects of actions',
    Root(J) 'root nodes of river-system (barriers with no downstream node)',
    RestorationFishes(F) 'set of target species for restoration',
    ControlFishes(F) 'set of target species for control/limitation';
alias
    (RestorationFishes,RF),
    (ControlFishes,CF);
parameter
    pass(J,F) 'current passability at barrier j for fish f',
    passChange(J,F) 'increase in passability due to barrier removal',
    habitat(J,F) 'current quality-adjusted habitat in area j for fish f',
    habitatChange(J,F) 'change in quality-adjusted habitat in area j for fish f',
    costRemoval(J) 'cost of removing barrier j',
    costControl(J) 'cost of controlling control species above barrier j',
    cap(F) 'max habitat for control species / min habitat for restoration species';
scalar
    budget 'management budget (barrier removal + control actions)',
    tradeoff 'weight on control species in objective to control relative contribution to objective' / 1e-3 /;


* LOAD MODEL DATA
$GDXIN %inputfile%
$load Fishes, Barriers, Downstream, Root, RestorationFishes, ControlFishes
$load pass, passChange, habitat, habitatChange, costRemoval, costControl, cap
$load budget
$gdxin


* CHECK DATA REQUIREMENTS

parameter cntHabMag 'Barrier/Fish pairs for which ||habitat|| < ||habitatChange|| which would violate model assumptions.';
cntHabMag = sum((J,F)$(abs(habitat(J,F)) < abs(habitatChange(J,F))), 1);
if (cntHabMag > 0, abort 'Magnitude of baseline habitat values must be larger than magnitude of habitat change with action.');



* VARIABLE AND EQUATION DECLARATIONS
free variable
    totalHabitat 'total weighted habitat across target species for entire system',
    cumPass(J,F) 'cumulative passability of barrier j for species f',
    cumHabitat(J,F) 'amount of accessible, quality-adjusted habitat above barrier j for fish t';
positive variable
    removalXcumPass(J,F) 'removalXcumPass(J) = removals(J)*cumPass(Downstream(J),F)',
    controlXcumPass(J,F) 'controlXcumPass(J) = controls(J)*cumPass(J,F)';
binary variable
    removals(J) 'remove barrier j: yes or no',
    controls(J) 'control the control species above barrier j: yes or no';

    
* EQUATION (MODEL) DEFINITION

equations
eq_objective 'first maximize restoration species habitat, secondarily minimize control species habitat',
eq_cumHabitat(J,F) 'calculate cumHabitat(j,t)',
eq_cumPass_root(J,F) 'calculate cumPass(j,t) at each root node',
eq_cumPass_upstream(J,K,F) 'calculate cumPass(j,t) at each upstream node',
cn_budget 'enforce habitat management budget constraint',
cn_cap_CF(F) 'limit available habitat for control species',
cn_cap_RF(F) 'enforce minimum habitat for restoration species',
cn_controlXcumPass_controls(J,F) 'turn controlXcumPass "on" only when control is applied',
cn_controlXcumPass_cumPass(J,F) 'set upper bound of controlXcumPass to cumPass(j,t)',
cn_removalXcumPass_removals(J,F) 'turn removalXcumPass "on" only when barrier is removed',
cn_removalXcumPass_cumPass(J,K,F) 'set upper bound of removalXcumPass to cumPass(Downstream(j),t)',
cn_removalXcumPass_upstream(J,K,F) 'enforce lower bound on removalXcumPass at each upstream node for control species';
*cn_controlXcumPass_equality(J,F) 'Check that controlXcumPass meets its equality constraint.';

eq_objective..
    totalHabitat =e= sum((J,RF), cumHabitat(J,RF)) - tradeoff * sum((J,CF), cumHabitat(J,CF));

eq_cumHabitat(J,F)..
    cumHabitat(J,F) =e= habitat(J,F)*cumPass(J,F) + habitatChange(J,F)*controlXcumPass(J,F);

eq_cumPass_root(J,F)$(Root(J))..
    cumPass(J,F) =e= pass(J,F) + passChange(J,F)*removals(J);

eq_cumPass_upstream(J,K,F)$(not Root(J) and Downstream(J,K))..
    cumPass(J,F) =e= pass(J,F)*cumPass(K,F) + passChange(J,F)*removalXcumPass(J,F);

cn_budget..
    sum(J, costRemoval(J)*removals(J) + costControl(J)*controls(J)) =l= budget;

cn_cap_CF(F)$(ControlFishes(F))..
    sum(J, cumHabitat(J,F)) =l= cap(F);

cn_cap_RF(F)$(RestorationFishes(F))..
    sum(J, cumHabitat(J,F)) =g= cap(F);

cn_controlXcumPass_controls(J,F)..
    controlXcumPass(J,F) =l= controls(J);

cn_controlXcumPass_cumPass(J,F)..
    controlXcumPass(J,F) =l= cumPass(J,F);

cn_removalXcumPass_removals(J,F)..
    removalXcumPass(J,F) =l= removals(J);

cn_removalXcumPass_cumPass(J,K,F)$(not Root(J) and Downstream(J,K))..
    removalXcumPass(J,F) =l= cumPass(K,F);

cn_removalXcumPass_upstream(J,K,F)$((not Root(J)) and ControlFishes(F) and Downstream(J,K))..
    removalXcumPass(J,F) =g= cumPass(K,F) + removals(J) - 1;

* Checked by Austin Milt 11/05/2015 and does not change results (appears to not be necessary)    
*cn_controlXcumPass_equality(J,F)..
*    controlXcumPass(J,F) =g= cumPass(J,F) + controls(J) - 1;

model fishHabitat /all/;


* SOLVE
option optcr = 1e-6;
fishHabitat.optfile=1;
fishHabitat.reslim = 3600;
fishHabitat.holdfixed = 1;
fishHabitat.limcol    = 0;
fishHabitat.limrow    = 0;

solve fishHabitat using mip max totalHabitat;
abort$(fishHabitat.SolveStat = %SolveStat.UserInterrupt%) 'job interrupted';


* DISPLAY SUMMARY RESULTS

parameter
    remainingBudget 'leftover budget',
    speciesHabitat(F) 'total available habitat for target species';
sets
    toRemove(J) "Barriers that should be removed",
    toControl(J) "Barriers that should have control actions",
    negHab(J,F) "Barrier/Fish pairs for which cumHabitat comes out negative which would require additional constraints";


removals.l(J) = round(removals.l(J));
toRemove(J) = yes$(removals.l(J));

controls.l(J) = round(controls.l(J));
toControl(J) = yes$(controls.l(J));

negHab(J,F) = yes$(cumHabitat.l(J,F) < 0);

remainingBudget = budget - sum(J, costRemoval(J)*removals.l(J) + costControl(J)*controls.l(J));

speciesHabitat(F) = sum(J, cumHabitat.l(J,F));

display totalHabitat.l;
option toRemove:0:0:2;
display toRemove;
option toControl:0:0:2;
display toControl;
display speciesHabitat;
display remainingBudget;
option negHab:0:0:2;
display negHab;
