# This file contains tests for the hydrography module

# Created 12/01/2015
# Updated 12/01/2015
# Author: Austin Milt
# ArcGIS version: 10.3.1
# Python version: 2.7.8

def __test__(verbose=False):

    from hydrography import Barrier, Reach, Catchment, Tributary, Lake

    # Test Data
    
    # Barriers
    BA = Barrier(id='BA', country='USA', fprop=0.1, passabilities={'04':1.0, '03':0.4})
    BB = Barrier(id='BB', country='USA', fprop=0.2, passabilities={'04':1.0, '03':0.4})
    BC = Barrier(id='BC', country='USA', fprop=0.3, passabilities={'04':1.0, '03':0.4})
    BD = Barrier(id='BD', country='USA', fprop=0.1, passabilities={'04':1.0, '03':0.4})
    BE = Barrier(id='BE', country='USA', fprop=0.2, passabilities={'04':1.0, '03':0.4})
    BF = Barrier(id='BF', country='USA', fprop=0.3, passabilities={'04':1.0, '03':0.4})
    BG = Barrier(id='BG', country='USA', fprop=0.4, passabilities={'04':1.0, '03':0.4})
    BH = Barrier(id='BH', country='USA', fprop=0.1, passabilities={'04':1.0, '03':0.4})
    BI = Barrier(id='BI', country='USA', fprop=0.2, passabilities={'04':1.0, '03':0.4})
    BJ = Barrier(id='BJ', country='USA', fprop=0.3, passabilities={'04':1.0, '03':0.4})
    BK = Barrier(id='BK', country='USA', fprop=0.1, passabilities={'04':1.0, '03':0.4})
    BL = Barrier(id='BL', country='USA', fprop=0.2, passabilities={'04':1.0, '03':0.4})
    BM = Barrier(id='BM', country='USA', fprop=0.1, passabilities={'04':1.0, '03':0.4})
    BN = Barrier(id='BN', country='USA', fprop=0.1, passabilities={'04':1.0, '03':0.4})
    BA.down = BB
    BB.down = BC
    BC.down = BH
    BD.down = BF
    BE.down = BF
    BF.down = BG
    BG.down = BJ
    BI.down = BJ
    BK.down = BL
    BL.down = BN
    BM.down = BN

    # Reaches
    RA = Reach(id='RA', length=1.1, barriers=set([BA]))
    RB = Reach(id='RB', length=1.2)
    RC = Reach(id='RC', length=1.3, barriers=set([BB, BC]))
    RD = Reach(id='RD', length=1.4)
    RE = Reach(id='RE', length=1.5)
    RF = Reach(id='RF', length=1.1, barriers=set([BD]))
    RG = Reach(id='RG', length=1.2, barriers=set([BE]))
    RH = Reach(id='RH', length=1.3, barriers=set([BF, BG]))
    RI = Reach(id='RI', length=1.1, barriers=set([BH]))
    RJ = Reach(id='RJ', length=1.2, barriers=set([BI]))
    RK = Reach(id='RK', length=1.3)
    RL = Reach(id='RL', length=1.4)
    RM = Reach(id='RM', length=1.5)
    RN = Reach(id='RN', length=1.6, barriers=set([BJ]))
    RO = Reach(id='RO', length=1.7)
    RP = Reach(id='RP', length=1.1, barriers=set([BK, BL]))
    RQ = Reach(id='RQ', length=1.1)
    RR = Reach(id='RR', length=1.2, barriers=set([BM]))
    RS = Reach(id='RS', length=1.3)
    RT = Reach(id='RT', length=1.1, barrieres=set([BN]))
    RU = Reach(id='RU', length=1.2)
    RV = Reach(id='RV', length=1.3)
    RA.down = RC
    RB.down = RC
    RC.down = RE
    RD.down = RE
    RE.down = RI
    RF.down = RH
    RG.down = RH
    RH.down = RK
    RI.down = RO
    RJ.down = RM
    RK.down = RM
    RL.down = RN
    RM.down = RN
    RN.down = RO
    RP.down = RQ
    RQ.down = RS
    RR.down = RS
    RS.down = RT
    RT.down = RV
    RU.down = RV

    # Catchments
    CA = Catchment(id='CA', area=10.1, reaches=set([RA, RB, RC, RD, RE]))
    CB = Catchment(id='CB', area=10.2, reaches=set([RF, RG, RH]))
    CC = Catchment(id='CC', area=10.1, reaches=set([RP]))
    CD = Catchment(id='CD', area=10.3, reaches=set([RI, RJ, RK, RL, RM, RN, RO]))
    CE = Catchment(id='CE', area=10.2, reaches=set([RQ, RR, RS]))
    CF = Catchment(id='CF', area=10.3, reaches=set([RT, RU, RV]))
    CA.down = CD
    CB.down = CD
    CC.down = CE
    CE.down = CF
    
    # Tributaries
    taReaches = CA.reaches.union(CB.reaches).union(CD.reaches)
    TA = Tributary(taReaches)
    tbReaches = CC.reaches.union(CE.reaches).union(CF.reaches)
    TB = Tributary(tbReaches)
    
    LA = Lake([TA, TB])
    
    # Tests
    epsilon = 1e5
    tests = (
        'RA.trace_down() == [RC, RE, RI, RO]', # reach's downstream trace is correct
        'CC.trace_down() == [CE, CF]', # catchment's down-stream trace is correct
        'BE.trace_down() == [BF, BG, BJ]', # barrier's down-stream trace is correct
        'RS.catchment.trace_up(RS) == set([RR, RQ])', # reach's up-catchment trace is correct
        'abs(CE.length_all() - (RS.length + RR.length + RQ.length)) < epsilon', # catchment's length_all is correct
        'abs(RO.catchment.length_up(RO, levels=2) - (RN.length + RM.length + RL.length + RI.length)) < epsilon', # catchment's length-up is correct
        'RG.catchment.length_down(RG) == RH.length', # catchment's length_down is correct
        'RM.tributary.trace_up(RM) == set([RG, RJ, RF, RK, RH])', # reach's up-tributary-trace is correct
        'CF.tributary.trace_up(CF) == set([CC, CE])', # catchment's up-tributary trace is correct
        'BJ.tributary.trace_up(BJ) == set([BI, BF, BD, BG, BE])', # barrier's up-tributary trace is correct
        'abs(CD.tributary.area_up(CD) - (CA.area + CB.area)) < epsilon', # tributary area_up is correct
        'CB.tributary.area_down(CB) == CD.area', # tributary area_down is correct
        'abs(RP.tributary.length_all() - sum([r.length for r in (RP, RQ, RR, RS, RT, RU, RV)])) < epsilon', # tributary's length_all is correct
        'abs(RM.tributary.length_up(RM) - sum([r.length for r in (RJ, RK, RH, RF, RG)])) < epsilon', # tributary's length_up is correct
        'abs(RM.tributary.length_down(RM) - sum([r.length for r in (RN, RO)])) < epsilon', # tributary's length_down is correct
        'abs(LA.area_all() - (CA.area + CB.area + CC.area + CD.area + CE.area + CF.area)) < epsilon', # sum of areas matches in area_all function
        'abs(LA.length_all() - sum([r.length for r in (RA, RB, RC, RD, RE, RF, RG, RH, RI, RJ, RK, RL, RM, RN, RO, RP, RQ, RR, RS, RT, RU, RV)])) < epsilon', # lake's length_all is correct
        'BJ.reach.trace_up(BJ) == set()', # barriers with no upstream barriers have empty upstream set
        'RL.tributary.length_up(RL) == 0.' # reaches without upstream reaches have up length == 0
    )
    failures = 0
    for test in tests:
        try:
            result = eval(test)
            if result == True:
                if verbose: print 'PASSED: %s' % test
            else:
                print 'FAILED: %s' % test
                failures += 1
            
        except Exception as e:
            print 'FAILED with Exception (%s): %s' % (str(e), test)
            failures += 1
            
    if failures > 0:
        import pdb; pdb.set_trace()