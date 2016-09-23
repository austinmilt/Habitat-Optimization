$title Habitat Optimization with Generic Barrier or Habitat Actions (Fishworks v6)
* Based on O'Hanley model formulation v2, model 1, modified to allow
*   multiple projects and differentiate candidate from non-candidate barriers

* DEFINE COMMAND-LINE OPTIONS

* input gdx
$if not set defaultgdx $set defaultgdx 'data_all.gdx'
$if not set rungdx $set rungdx 'data_run.gdx'


* SETS AND DEFINITIONS

sets
    Targets(*) 'set of targets to be affected by project actions',
    Guilds(*) 'names of passability guilds to which targets belong',
    Barriers(*) 'set of barriers dams/road culverts in the network (by ID number)',
    Projects(*) 'projects that can be done to affect barrier passability or upstream benefit potential',
    BudgetNames(*) 'spending budgets from which projects can draw money';
alias
    (Targets,T),
    (Guilds,G),
    (Barriers,J,K),
    (Projects,P),
    (BudgetNames,B);
sets
    Downstream(J,K) 'K is the barrier immediately downstream from J; used for tracing upstream/downstream effects of actions',
    TargetToGuild(T,G) 'mapping from targets to passability guild to reduce passability constraints',
    GuildsBeneficiary(G) 'set of guilds for beneficiary targets',
    GuildsControl(G) 'set of guilds for control targets',
    ProjectsBenefit(P) 'projects that affect potential benefit',
    ProjectsPassability(P) 'projects that affect barrier passability',
    ProjectToBudget(P,B) 'budget from which project draws money';
alias
    (GuildsBeneficiary,GB),
    (GuildsControl,GC),
    (ProjectsBenefit,PB)
    (ProjectsPassability,PP);
parameter
    isCandidate(J,P) 'Boolean indicating that a barrier is a candidate for a project',
    isRoot(J) 'Boolean indicating that a barrier is a root barrier (has no downstream barriers)',
    passBase(J,G) 'current passability at barrier j for guild g',
    passChange(J,P,G) 'change in passability for guild g by doing project p at barrier j',
    benefitMaxBase(J,T) 'baseline potential quality-adjusted benefit above barrier j for target t',
    benefitMaxChange(J,P,T) 'change in potential quality-adjusted benefit in area j for target t from doing project p',
    cost(J,P) 'cost of doing project p at barrier J',
    cap(T) 'max (min) allowed accessibility-weighted benefit for control targets (beneficiary targets)',
    weight(T) 'weight/priority of target t',
    budget(B) 'budget amounts from which projects draw money';
scalar
    obj2Weight 'weight on secondary objective (here to do with control targets)';


* LOAD MODEL DATA
$GDXIN %defaultgdx%
$load Targets, Barriers, Projects, BudgetNames, Guilds
$gdxin

$GDXIN %rungdx%
$loadm Targets, Barriers, Projects, BudgetNames, Guilds
$gdxin

$GDXIN %defaultgdx%
$load Downstream, ProjectsPassability, GuildsBeneficiary, GuildsControl
$load ProjectsBenefit, passBase, passChange, benefitMaxBase
$load benefitMaxChange, cost, budget, weight, cap, ProjectToBudget, obj2Weight
$load isCandidate, isRoot, TargetToGuild
$gdxin

$GDXIN %rungdx%
$loadm Downstream, ProjectsPassability, GuildsBeneficiary, GuildsControl
$loadm ProjectsBenefit, passBase, passChange, benefitMaxBase
$loadm benefitMaxChange, cost, budget, weight, cap, ProjectToBudget, obj2Weight
$loadm isCandidate, isRoot, TargetToGuild
$gdxin


* CHECK DATA REQUIREMENTS
parameter
    cntHabMag 'Barrier/Fish pairs for which ||benefitMaxBase|| < ||benefitMaxChange|| which would violate model assumptions.',
    possiblePassability(J,G) 'total possible passability of a barrier for a target',
    cntEffOOB 'number of Target/Barrier pairs for which the total possible passability is outside [0, 1], which violates assumptions';

cntHabMag = sum((J,P,T)$(abs(benefitMaxBase(J,T)) < abs(benefitMaxChange(J,P,T))), 1);
if (cntHabMag > 0, abort 'Magnitude of baseline benefitMaxBase values must be larger than magnitude of benefitMaxBase change with action.');
possiblePassability(J,G) = passBase(J,G) + sum(P$(ProjectsPassability(P)), passChange(J,P,G));
cntEffOOB = sum((J,G)$((possiblePassability(J,G) > (1.00001)) or (possiblePassability(J,G) < (-0.00001))), 1);
if (cntEffOOB > 0, abort 'Total possible passability for a guild at a barrier must be in the closed interval [0, 1].');


* VARIABLE AND EQUATION DECLARATIONS
set
    Candidates(J, P) 'set of candidate barriers for removal',
    Root(J) 'root nodes of river-system (barriers with no downstream node)';
free variable
    totalBenefit 'total weighted benefit across targets for entire system',
    cumPass(J,G) 'cumulative passability of barrier j for guild g',
    cumBenBar(J,T) 'accessibility-weighted benefit at barrier j for target t';
positive variable
    action_benXcumPass(J,P,G) 'action_benXcumPass(J,P,G) = actions(J,benefit_actions P)*cumPass(Downstream(J),G)',
    action_passXcumPass(J,P,G) 'action_passXcumPass(J,P,G) = actionBen(J, passability_actions P)*cumPass(J,G)';
binary variable
    actions(J,P) 'perform project p at barrier j: yes or no';

* set up derived parameters from inputs
Candidates(J,P) = yes$(isCandidate(J,P));
Root(J) = yes$(isRoot(J));


* EQUATION (MODEL) DEFINITION

equations
eq_objective 'first maximize beneficiary targets benefits, secondarily minimize control targets benefits',
eq_cumBenBar(J,T) 'calculate cumBenBar(j,t)',
eq_cumPass_root(J,G) 'calculate cumPass(j,t) at each root node',
eq_cumPass_upstream(J,K,G) 'calculate cumPass(j,t) at each upstream node',
cn_budget(B) 'enforce budget constraints',
cn_cap_GC(T,G) 'limit available accessibility-weighted benefit for control targets',
cn_cap_GB(T,G) 'enforce minimum accessibility-weighted benefit for beneficiary targets',
cn_action_benXcumPass_actionBen(J,P,G) 'first part of probability chain to linearize action_benXcumPass',
cn_action_benXcumPass_cumPass(J,P,G) 'second part of probability chain to linearize action_benXcumPass',
cn_action_passXcumPass_actionPass(J,P,G) 'first part of probability chain to linearize action_passXcumPass',
cn_action_passXcumPass_Root(J,P,G) 'second part of probability chain to linearize action_passXcumPass',
cn_action_passXcumPass_cumPass(J,K,P,G) 'third part of probability chain to linearize action_passXcumPass',
cn_action_passXcumPass_upstream(J,K,P,G) 'third part of probability chain to linearize action_passXcumPass, specific for upstream nodes and control targets';
*cn_controlXcumPass_equality(J,T) 'Check that action_benXcumPass meets its equality constraint.';

eq_objective..
    totalBenefit =e= sum((T,G)$(GB(G) and TargetToGuild(T,G)), weight(T)*sum(J, cumBenBar(J,T))) + obj2Weight*sum((T,G)$(GC(G) and TargetToGuild(T,G)), weight(T)*sum(J, cumBenBar(J,T)));
* totalBenefit =e= sum((J,T)$(TargetToGuild(T,G)$(GB(G))), weight(T)*cumBenBar(J,T)) + obj2Weight*sum((J,T)$(TargetToGuild(T,G)$(GC(G))), weight(T)*cumBenBar(J,T));

eq_cumBenBar(J,T)..
    cumBenBar(J,T) =e= sum(G$(TargetToGuild(T,G)), benefitMaxBase(J,T)*cumPass(J,G) + sum(PB(P), benefitMaxChange(J,PB,T)*action_benXcumPass(J,PB,G)));
* cumBenBar(J,T) =e= benefitMaxBase(J,T)*cumPass(J,G)$(TargetToGuild(T,G)) + sum(PB(P), benefitMaxChange(J,PB,T)*action_benXcumPass(J,PB,G)$(TargetToGuild(T,G)));

eq_cumPass_root(J,G)$(Root(J))..
    cumPass(J,G) =e= passBase(J,G) + sum(PP(P), passChange(J,PP,G)*actions(J,PP));
*   cumPass(J,T) =e= passBase(J,T) + sum(ProjectsPassability(P), passChange(J,PP,T)*action_passXcumPass(J,PP,T));

eq_cumPass_upstream(J,K,G)$((not Root(J)) and Downstream(J,K))..
    cumPass(J,G) =e= passBase(J,G)*cumPass(K,G) + sum(PP(P), passChange(J,PP,G)*action_passXcumPass(J,PP,G));

cn_budget(B)..
    sum((J,P)$(Candidates(J,P) and ProjectToBudget(P,B)), cost(J,P)*actions(J,P)) =l= budget(B);

cn_cap_GC(T,G)$(TargetToGuild(T,G)$(GC(G)))..
    sum(J, cumBenBar(J,T)) =l= cap(T);

cn_cap_GB(T,G)$(TargetToGuild(T,G)$(GB(G)))..
    sum(J, cumBenBar(J,T)) =g= cap(T);

cn_action_benXcumPass_actionBen(J,P,G)$(ProjectsBenefit(P))..
    action_benXcumPass(J,P,G) =l= actions(J,P);

cn_action_benXcumPass_cumPass(J,P,G)$(ProjectsBenefit(P))..
    action_benXcumPass(J,P,G) =l= cumPass(J,G);

cn_action_passXcumPass_actionPass(J,P,G)$(ProjectsPassability(P))..
    action_passXcumPass(J,P,G) =l= actions(J,P);

cn_action_passXcumPass_Root(J,P,G)$(Root(J) and GuildsControl(G) and ProjectsPassability(P))..
    action_passXcumPass(J,P,G) =g= actions(J,P);
* Austin Milt 02/11/2015 The specification for GuildsControl at Roots is
*   necessary to enforce non-negative passabilities for GuildsControl
*   throughout the network

cn_action_passXcumPass_cumPass(J,K,P,G)$((not Root(J)) and Downstream(J,K) and ProjectsPassability(P))..
    action_passXcumPass(J,P,G) =l= cumPass(K,G);

cn_action_passXcumPass_upstream(J,K,P,G)$((not Root(J)) and GuildsControl(G) and Downstream(J,K) and ProjectsPassability(P))..
    action_passXcumPass(J,P,G) =g= cumPass(K,G) + actions(J,P) - 1;

* Checked by Austin Milt 11/05/2015 and does not change results (appears to not be necessary)
*cn_controlXcumPass_equality(J,T)..
*    action_benXcumPass(J,T) =g= cumPass(J,T) + actionBen(J) - 1;


* INITIAL SOLVE WITH GUROBI
model fishHabitat /all/;
option MIP = gurobi;
option optcr = 0.1;
option reslim = 3600;
option solvelink = 0;
fishHabitat.optfile=1;
fishHabitat.reslim = 3600;
fishHabitat.holdfixed = 1;
fishHabitat.limcol    = 0;
fishHabitat.limrow    = 0;

* fix all non-candidate barrier passChange and benMaxChange to 0 to avoid
*   having them selected for removal or treatment
passChange(J,P,G)$(not Candidates(J,P)) = 0;
actions.fx(J,P)$(not Candidates(J,P)) = 0;
benefitMaxChange(J,P,T)$(not Candidates(J,P)) = 0;

solve fishHabitat using mip max totalBenefit;
abort$(fishHabitat.SolveStat = %SolveStat.UserInterrupt%) 'job interrupted';
solve fishHabitat using mip max totalBenefit;
abort$(fishHabitat.SolveStat = %SolveStat.UserInterrupt%) 'job interrupted';
solve fishHabitat using mip max totalBenefit;
abort$(fishHabitat.SolveStat = %SolveStat.UserInterrupt%) 'job interrupted';


* SECONDARY SOLVE WITH RESULTS FROM GUROBI, USING CPLEX
option MIP = cplex;
option reslim = 3600;
fishHabitat.reslim = 3600;
solve fishHabitat using mip max totalBenefit;
abort$(fishHabitat.SolveStat = %SolveStat.UserInterrupt%) 'job interrupted';


* DISPLAY SUMMARY RESULTS

parameter
    remainingBudget(B) 'leftover budget',
    speciesHabitat(T) 'total available benefitMaxBase for target species',
    gap 'relative optimality gap of solution',
    solve_time 'time taken to build and solve the model (timeExec)';
sets
    doActions(J,P) "Barriers that should be removed",
    negHab(J,T) "Barrier/Fish pairs for which cumBenBar comes out negative which would require additional constraints";


actions.l(J,P) = round(actions.l(J,P));
doActions(J,P) = yes$(actions.l(J,P));

negHab(J,T) = yes$(cumBenBar.l(J,T) < -1e-6);

remainingBudget(B) = budget(B) - sum((J,P)$(Candidates(J,P) and ProjectToBudget(P,B)), cost(J,P)*actions.l(J,P));

speciesHabitat(T) = sum(J, cumBenBar.l(J,T));

gap = 1 - (fishHabitat.objVal / fishHabitat.objEst);

solve_time = timeExec;

display totalBenefit.l;
option doActions:0:0:2;
display doActions;
display speciesHabitat;
display remainingBudget;
option negHab:0:0:2;
display negHab;
display gap;
display solve_time;

* WRITE OUTPUT GDX
Execute_Unload 'results',
    totalBenefit.l=objective, doActions=actions, speciesHabitat=target_benefits,
    remainingBudget=remaining_budget, negHab=negative_benefits, gap=optimality_gap,
    solve_time, budget, cap, weight;