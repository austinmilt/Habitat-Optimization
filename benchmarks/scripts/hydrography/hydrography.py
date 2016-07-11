# This is the main file that defines classes to create a hydrology network
#   with barriers, linked classes and attributes

# Created 11/23/2015
# Updated 12/01/2015
# Author: Austin Milt
# ArcGIS version: 10.3.1
# Python version: 2.7.8
            

# ~~ GLOBAL CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# OrderedObject
ORD_DID = 0

# Reach
RCH_LEN = None
RCH_SIZ = None

# Structure
STR_FPR = 0.0

# Barrier
BAR_CST = None

# Dam
DAM_WID = None
DAM_LEN = None
DAM_HIT = None

# RSX
RSX_WID = None
RSX_LEN = None
RSX_DRP = None
RSX_BFW = None

# OrderedCollection

# Catchment
CAT_ARE = None


# create_hydrography()
CRH_DAT_BAR = 'barriers'
CRH_DAT_FLO = 'flowlines'
CRH_DAT_CAT = 'catchments'
CRH_DAT_TRB = 'tributaries'
CRH_FLD_BID = 'bid'
CRH_FLD_BDS = 'bds'
CRH_FLD_RID = 'rid'
CRH_FLD_NAT = 'nation'
CRH_FLD_LAK = 'lake'
CRH_FLD_FPR = 'fprop'
CRH_FLD_HAB = 'habitat'
CRH_FLD_CST = 'cost'
CRH_FLD_LAM = 'lamp'
CRH_FLD_P04 = 'passlow'
CRH_FLD_P07 = 'passmid'
CRH_FLD_P10 = 'passhigh'
CRH_FLD_BFW = 'bfw'
CRH_FLD_DRP = 'drop'
CRH_FLD_HIT = 'height'
CRH_FLD_WID = 'width'
CRH_FLD_BLN = 'length'
CRH_FLD_TYP = 'isdam'
CRH_FLD_RDS = 'rds'
CRH_FLD_TID = 'tid'
CRH_FLD_CAT = 'cid'
CRH_FLD_CDS = 'cds'
CRH_FLD_WSA = 'area'
CRH_FLD_LEN = 'length'
CRH_FLD_STO = 'size'


# ########################################################################### #
# ########################## SINGLE UNITS ################################### #
# ########################################################################### #

# ~~ ORDERED OBJECT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class OrderedObject(object):
    """
    Basic hydrologic object with one downstream OrderedObject and at least one
    upstream OrderedObject.
    """
    
    def __init__(self, id=ORD_DID, **attributes):
        
        # set attributes using defaults and user overrides
        P = {
            'down': self, # next downstream OrderedObjects
        }
        P['id'] = id
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for k in P: setattr(self, k, P[k])
        

    def __eq__(self, other):
        if self is other: return True
        else: return False
            

    def trace_down(self, levels=None, filters=None, types=None):
        """
        Traces downstream of this object and returns all downstream
        objects
        
        INPUTS:
            levels  = (optional) number of levels to trace downstream. Default
                (None) is all levels until the last object is reached.
                
            filters = (optional) like levels, but stops after attributes
                of upstream objects no longer match the filter. Supply as
                a dict of attribute names with filter values as values. Default
                (None) is no filter.
                
            types   = (optional) list, set, or tuple of types to return. Can 
                be any type with OrderedObject parent class. Default is any 
                OrderedObject
                
        OUTPUTS: ordered list of all downstream OrderedObjects
        """
        
        
        # define filter test
        def filter_test(obj):
            if filters is None: return True
            return all([obj.__dict__[k] == filters[k] for k in filters])
        
        # trace down
        if types is None: types = OrderedObject
        if not hasattr(types, '__iter__'): types = (types,)
        curObj = self
        downstreamObjects = []
        count = 0
        while (curObj.down is not curObj) and any((count < levels, levels is None)) and filter_test(curObj.down):
            count += 1
            if isinstance(curObj.down, types):
                downstreamObjects.append(curObj.down)
            
            curObj = curObj.down
            
        return downstreamObjects
        
        
    def __setattr__(self, attribute, value):
    
        # error checking
        if attribute == 'down':
            if not isinstance(value, OrderedObject):
                raise TypeError('Downstream objects must be a sub-class of OrderedObject.')
                
        # handle other attribute assignments
        self.__dict__[attribute] = value
        
        
    def __repr__(self):
        return '%s %s' % (self.__class__.__name__, str(self.id))
        
    
    
# ~~ STRUCTURE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #            
class Structure(OrderedObject):
    """
    Structure is a stationary structure in a water body with hydrologic
    properties.
    """
    
    def __init__(self, **attributes):
    
        OrderedObject.__init__(self, **attributes)
        
        # set attributes using defaults and user overrides
        P = {
            'fprop': STR_FPR, # proportion along reach
            'reach': None, # Reach object on which self is found
            'country': None, # country in which self is found
            'tributary': None # tributary along which self is found
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
        
        
    def __setattr__(self, attribute, value):
    
        super(Structure, self).__setattr__(attribute, value)
        
        if attribute == 'fprop':
            if (value < 0) or (value > 1):
                raise ValueError('fprop attribute must be between 0 and 1.')
            
        self.__dict__[attribute] = value
        
        
            
# ~~ BARRIER ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Barrier(Structure):
    """
    Barriers are one type of Structure that create impediments to fish
    movement.
    """
    
    def __init__(self, **attributes):
        Structure.__init__(self, **attributes)
        
        # set attributes using defaults and user overrides
        P = {
            'passabilities': {}, # dictionary where keys are fish/guilds and values are passabilities
            'cost': BAR_CST # cost of making barrier totally passable (be e.g. removal)
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])

    
    def __setattr__(self, attribute, value):
        
        super(Barrier, self).__setattr__(attribute, value)
        
        if attribute == 'passabilities':
            for k in value:
                if (value[k] < 0) or (value[k] > 1):
                    raise ValueError('passabilities must be between 0 and 1.')
            
        self.__dict__[attribute] = value

        
        
# ~~ DAM ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Dam(Barrier):
    """
    Dams are one type of Barrier with built in dimensional attributes.
    """
    
    def __init__(self, **attributes):
        Barrier.__init__(self, **attributes)
    
        # set attributes using defaults and user overrides
        P = {
            'width': DAM_WID, # up- to down-stream width of dam
            'height': DAM_HIT, # vertical height of dam
            'length': DAM_LEN # river spanning length of dam
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
    
    
    def __setattr__(self, attribute, value):
    
        super(Dam, self).__setattr__(attribute, value)
        
        if attribute in ('width', 'height', 'length'):
            if (value is not None) and (value < 0):
                raise ValueError('Dam dimensions must be non-negative.')
    
    
        self.__dict__[attribute] = value
        
        
        
# ~~ RSX ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class RSX(Barrier):
    """
    RSX are road stream crossings and are one type of Barrier with built in 
    dimensional attributes.
    """
    
    def __init__(self, **attributes):
        Barrier.__init__(self, **attributes)
    
        # set attributes using defaults and user overrides
        P = {
            'width': RSX_WID, # up- to down-stream width of road
            'drop': RSX_DRP, # vertical height of dam
            'length': RSX_LEN, # river spanning length of rsx
            'bfw': RSX_BFW, # bankfull width of the stream at the crossing
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
    
    
    def __setattr__(self, attribute, value):
        
        super(RSX, self).__setattr__(attribute, value)
        
        if attribute in ('width', 'drop', 'length', 'bfw'):
            if (value is not None) and (value < 0):
                raise ValueError('RSX dimensions must be non-negative.')
    
    
        self.__dict__[attribute] = value
            

            
# ########################################################################### #
# ########################### COLLECTIONS ################################### #
# ########################################################################### #

# ~~ ORDERED COLLECTION ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class OrderedCollection(OrderedObject):
    """
    OrderedCollection is a collection of OrderedObjects with methods to contain
    and trace along elements.
    """

    def __init__(self, objects, **attributes):
    
        OrderedObject.__init__(self, **attributes)
        
        # add objects to the set
        self.objects = set()
        for obj in objects:    
            if not isinstance(obj, OrderedObject):
                raise TypeError('OrderedCollections can only contain OrderedObjects.')
            self.objects.add(obj)
        self.first_up()
        
        
    def __setattr__(self, attribute, value):
        
        super(OrderedCollection, self).__setattr__(attribute, value)
        
        if attribute == 'up':
            print 'Use the first_up() method to set the up{} dictionary.'
        
        else:
            self.__dict__[attribute] = value

    
    def first_up(self, upAttr='up', objectAttr='objects'):
        """
        Initializes upstream tracing by finding the set of nearest upstream
        objects for each object. Sets the up dictionary in place.
        
        INPUTS:
            upAttr  = (optional) attribute name for the first_up dictionary.
                Default is 'up'. Used for OrderedCollections with more than
                one set of OrderedObjects.
                
            objectAttr = (optional) attribute name of the objects to perform
                calculations on. Default is 'objects'. Used for 
                OrderedCollections with more than one set of OrderedObjects.
                
        OUTPUTS: nothing. Modified in-place
        """
        self.__dict__[upAttr] = {}
        up = self.__dict__[upAttr]
        for obj in self.__dict__[objectAttr]:
            if obj not in up: up[obj] = set()
            if obj.down not in up: up[obj.down] = set()
            if obj.down is not obj: up[obj.down].add(obj)
        
    
    def trace_up(
        self, startingObject, levels=None, filters=None, 
        types=(OrderedObject,), upAttr='up'
        
    ):
        """
        Traces upstream from an object to all its upstream objects of a
        specified type.
        
        INPUTS:
            levels  = (optional) number of levels to trace upstream. Default
                (None) is all levels until the first object is reached.
                
            filters = (optional) like levels, but stops after attributes
                of upstream objects no longer match the filter. Supply as
                a dict of attribute names with filter values as values. Default
                (None) is no filter.
                
            types   = (optional) list, set, or tuple of types to return. Can 
                be any type with OrderedObject parent class. Default is any 
                OrderedObject
                
            upAttr  = (optional) attribute name for the first_up dictionary.
                Default is 'up'. Used for OrderedCollections with more than
                one set of OrderedObjects.
                
        OUTPUTS: set of all upstream objects of the starting object
        """
        
        # define filter test
        def filter_test(obj):
            if filters is None: return True
            return all([obj.__dict__[k] == filters[k] for k in filters])
        
        # trace
        up = self.__dict__[upAttr]
        toTrace = [(obj, 0) for obj in up[startingObject] if filter_test(obj)]
        upstreamObjects = set()
        while (len(toTrace) > 0) and any((toTrace[0][1] < levels, levels is None)):
            obj, level = toTrace.pop(0)
            if isinstance(obj, types):
                upstreamObjects.add(obj)
                
            # update remaining trace list
            toTrace.extend([(newObj, level+1) for newObj in up[obj] if filter_test(obj)])
        
        return upstreamObjects
        
        
    @staticmethod
    def __operate_over__(objects, attribute, operation='+', ignoreNone=True):
        """
        Operates over the attribute of the objects in the list, optionally 
        ignoring objects with an undefined attribute.
        
        INPUTS:
            objects     = list or set of objects to operate over
            
            attribute   = attribute of the objects from which values are used
                in operation
                
            operation   = (optional) operation to perform. Currently supported
                operations are '+' for addition and '*' for multiplication.
                
            ignoreNone  = (optional) flag to indicate to skip (True) objects
                when they dont have the attribute defined versus failing
                (False)
                
        OUTPUTS: result of the operation
        """
        ignoreTest = lambda x: ignoreNone or (x is not None)
        values = [obj.__dict__[attribute] for obj in objects]
        if operation == '+':
            return sum(values)
        elif operation == '*':
            prod = 1.
            for v in values: prod *= v
            return prod
    


# ~~ REACH ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Reach(OrderedCollection):
    """
    Reach is a segment of river and collects barriers.
    """
    
    def __init__(self, barriers=set(), **attributes):
        OrderedCollection.__init__(self, barriers, **attributes)
    
        # set attributes using defaults and user overrides
        P = {
            'length': RCH_LEN, # reach segment length
            'size': RCH_SIZ, # reach size (stream order)
            'catchment': None, # Catchment in which self is found
            'tributary': None # Tributary in which self is found
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
            
        # assign barriers their reach
        self.barriers = self.objects
        for barrier in self.barriers:
            barrier.reach = self

    
    
    
# ~~ CATCHMENT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Catchment(OrderedCollection):
    """
    Catchment is an OrderedCollection for reaches within a tributary, where
    reaches start and end within the catchment.
    """
    
    def __init__(self, reaches=set(), **attributes):
        
        OrderedCollection.__init__(self, reaches, **attributes)
        
        # set attributes using defaults and user overrides
        P = {
            'area': CAT_ARE, # watershed drainage area of self
            'tributary': None # Tributary along which self is located
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
        
        # update reach catchment identity
        self.reaches = self.objects
        for reach in self.reaches: reach.catchment = self
        
        
    def length_all(self, ignoreNone=True):
        """
        Calculates the total length of reaches within the catchment, optionally 
        ignoring reaches with an undefined length.
        """
        return self.__operate_over__(self.reaches, 'length', '+', ignoreNone)
        
        
    def length_up(self, reach, levels=None, ignoreNone=True):
        """
        Calculates the length of the Tributary upstream of the given reach
        within the catchment, optionally ignoring reaches with an undefined
        length.
        
        INPUTS:
            reach       = starting reach to calculate upstream length from
            levels      = (optional) see OrderedCollection.trace_up()
            ignoreNone  = (optional) whether to skip (True) when encountering
                reaches with an undefined length. Default is True.
                
        OUTPUTS: float of the total length upstream of the reach
        """
        upstreamReaches = self.trace_up(
            reach, levels, filters={'catchment': self}, types=Reach
        )
        return self.__operate_over__(upstreamReaches, 'length', '+', ignoreNone)
        
        
    def length_down(self, reach, levels=None, ignoreNone=True):
        """
        Calculates the length of the Tributary downstream of the given reach
        within the catchment, optionally ignoring reaches with an undefined 
        length.
        
        INPUTS:
            reach       = starting reach to calculate downstream length from
            levels      = (optional) see OrderedObject.trace_down()
            ignoreNone  = (optional) whether to skip (True) when encountering
                reaches with an undefined length. Default is True.
                
        OUTPUTS: float of the total length downstream of the reach
        """
        downstreamReaches = reach.trace_down(
            levels, filters={'catchment': self}, types=Reach
        )
        return self.__operate_over__(downstreamReaches, 'length', '+', ignoreNone)

        
        
        
# ~~ TRIBUTARY ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Tributary(OrderedCollection):
    """
    Tributary is a collection of reaches that spans catchments and drains
    into a lake.
    """
    
    def __init__(self, reaches, **attributes):
        
        OrderedCollection.__init__(self, reaches, **attributes)
        
        # set attributes using defaults and user overrides
        P = {
            'lake': None, # lake into which self drains
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
        
        # update catchment tributary identity and assign catchments for self
        self.reaches = self.objects
        self.catchments = set()
        self.barriers = set()
        for reach in self.reaches:
            reach.catchment.tributary = self
            self.catchments.add(reach.catchment)
            reach.tributary = self
            
            for barrier in reach.barriers:
                barrier.tributary = self
                self.barriers.add(barrier)
            
        # update the first upstream object dictionaries
        del self.up
        self.first_up('catchUp', 'catchments')
        self.first_up('reachUp', 'reaches')
        self.first_up('barUp', 'barriers')
            
            
    def trace_up(self, startingObject, levels=None, filters=None):
        """
        See OrderedCollection.trace_up, except types and upAttr are
        automatically determined.
        """
        if isinstance(startingObject, Reach):
            return super(Tributary, self).trace_up(startingObject, levels, filters, (Reach,), 'reachUp')
            
        elif isinstance(startingObject, Catchment):
            return super(Tributary, self).trace_up(startingObject, levels, filters, (Catchment,), 'catchUp')
        
        elif isinstance(startingObject, Structure):
            return super(Tributary, self).trace_up(startingObject, levels, filters, (Structure,), 'barUp')
            
    
    def area_all(self, ignoreNone=True):
        """
        Calculates the total area of catchements the tributary spans, optionally 
        ignoring catchments with an undefined area.
        """
        return self.__operate_over__(self.catchments, 'area', '+', ignoreNone)
        
        
    def area_up(self, catchment, levels=None, ignoreNone=True):
        """
        Calculates the area of the catchments upstream of the given catchment
        the tributary spans, optionally ignoring reaches with an undefined
        length.
        
        INPUTS:
            catchment   = starting catchment to calculate upstream area from
            levels      = (optional) see OrderedCollection.trace_up()
            ignoreNone  = (optional) whether to skip (True) when encountering
                catchments with an undefined area. Default is True.
                
        OUTPUTS: float of the total area upstream of the catchment
        """
        upstreamCatchments = self.trace_up(
            catchment, levels, filters={'tributary': self}
        )
        return self.__operate_over__(upstreamCatchments, 'area', '+', ignoreNone)
        
        
    def area_down(self, catchment, levels=None, ignoreNone=True):
        """
        Calculates the area of the catchments downstream of the given catchment
        the tributary spans, optionally ignoring catchments with an undefined 
        area.
        
        INPUTS:
            catchment       = starting reach to calculate downstream length from
            levels      = (optional) see OrderedObject.trace_down()
            ignoreNone  = (optional) whether to skip (True) when encountering
                reaches with an undefined length. Default is True.
                
        OUTPUTS: float of the total length downstream of the reach
        """
        downstreamCatchments = catchment.trace_down(
            levels, filters={'tributary': self}, types=Catchment
        )
        return self.__operate_over__(downstreamCatchments, 'area', '+', ignoreNone)
        
        
    def length_all(self, ignoreNone=True):
        """
        Calculates the total length of reaches within the tributary, optionally 
        ignoring reaches with an undefined length.
        """
        return self.__operate_over__(self.reaches, 'length', '+', ignoreNone)
        
        
    def length_up(self, reach, levels=None, ignoreNone=True):
        """
        Calculates the length of the Tributary upstream of the given reach
        within the tributary, optionally ignoring reaches with an undefined
        length.
        
        INPUTS:
            reach       = starting reach to calculate upstream length from
            levels      = (optional) see OrderedCollection.trace_up()
            ignoreNone  = (optional) whether to skip (True) when encountering
                reaches with an undefined length. Default is True.
                
        OUTPUTS: float of the total length upstream of the reach
        """
        upstreamReaches = self.trace_up(
            reach, levels, filters={'tributary': self}
        )
        return self.__operate_over__(upstreamReaches, 'length', '+', ignoreNone)
        
        
    def length_down(self, reach, levels=None, ignoreNone=True):
        """
        Calculates the length of the Tributary downstream of the given reach
        within the catchment, optionally ignoring reaches with an undefined 
        length.
        
        INPUTS:
            reach       = starting reach to calculate downstream length from
            levels      = (optional) see OrderedObject.trace_down()
            ignoreNone  = (optional) whether to skip (True) when encountering
                reaches with an undefined length. Default is True.
                
        OUTPUTS: float of the total length downstream of the reach
        """
        downstreamReaches = reach.trace_down(
            levels, filters={'tributary': self}, types=Reach
        )
        return self.__operate_over__(downstreamReaches, 'length', '+', ignoreNone)
        
        
        
# ~~ LAKE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Lake(OrderedCollection):
    
    def __init__(self, tributaries, **attributes):
        
        OrderedCollection.__init__(self, tributaries, **attributes)
        
        # set attributes using defaults and user overrides
        P = {}
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
        self.tributaries = self.objects
        
        # update tributary lake identity
        for tributary in self.tributaries: tributary.lake = self
 
    
    def length_all(self, ignoreNone=True):
        """
        Calculates the total length of tributaries draining into the lake,
        optionally ignoring reaches with undefined lengths.
        """
        return sum([trib.length_all(ignoreNone) for trib in self.tributaries])
        
        
    def area_all(self, ignoreNone=True):
        """
        Calculates the total ara of all catchments draining into self,
        optionally ignoring catchments with undefined area.
        """
        return sum([trib.area_all(ignoreNone) for trib in self.tributaries])
        
        
        
# ~~ HYDROGRAPHY ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Hydrography(object):
    """
    Hydrography is a simple collection of Lakes with methods to access all
    features of a certain type, and also automatically processes formatted
    inputs to create the hydrography object.
    """
    
    def __init__(self, data, **attributes):
        
        # set self attributes
        for k in attributes: setattr(self, k, attributes[k])
        self.__process_data__(data)
            
        
    def __process_data__(self, data):
        """Processes formatted data as returned by load_data and modifies self."""
        
        # ~~ CREATE BARRIERS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        fields, table = data[CRH_DAT_BAR]
        barriers = {}
        passabilityFields = (CRH_FLD_P04, CRH_FLD_P07, CRH_FLD_P10) 
        reachBarriers = {}
        for row in table:
            oid = row[fields[CRH_FLD_BID]]
            passabilities = dict((k, row[fields[k]]) for k in passabilityFields)
            attributes = {
                'id': oid, 'fprop': row[fields[CRH_FLD_FPR]], 
                'country': row[fields[CRH_FLD_NAT]],
                'cost': row[fields[CRH_FLD_CST]], 'passabilities': passabilities
            }
            
            # optional fields
            if CRH_FLD_WID in fields:
                attributes['width'] = row[fields[CRH_FLD_HIT]]
            if CRH_FLD_BLN in fields:
                attributes['length'] = row[fields[CRH_FLD_BLN]]
                    
            # dam specific attributes and create Dam
            isDam = row[fields[CRH_FLD_TYP]]
            if isDam:
                attributes['height'] = row[fields[CRH_FLD_HIT]]
                barrier = Dam(**attributes)
            
            # RSX specific attributes and create RSX
            else:
                attributes['drop'] = row[fields[CRH_FLD_HIT]]
                attributes['bfw'] = row[fields[CRH_FLD_BFW]]
                barrier = RSX(**attributes)
                
            # add to barriers set and also keep track of the other
            #   necessary info (downstream id and reach id)
            barriers[oid] = (
                barrier, row[fields[CRH_FLD_BDS]]
            )
            
            # record set of barriers for each reach
            rid = row[fields[CRH_FLD_RID]]
            if rid not in reachBarriers:
                reachBarriers[rid] = []
            reachBarriers[rid].append(barrier)
                
        # set barrier downstream objects
        for oid in barriers:
            if barriers[oid][1] is None: barriers[oid][0].down = barriers[oid][0]
            else: barriers[oid][0].down = barriers[barriers[oid][1]][0]
        
        
        # ~~ CREATE REACHES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # create reaches that contain barriers
        fields, table = data[CRH_DAT_FLO]
        reaches = {}
        catchmentReaches = {}
        tributaryReaches = {}
        for row in table:
        
            # define basic attributes
            oid = row[fields[CRH_FLD_RID]]
            attributes = {
                'id': oid, 'length': row[fields[CRH_FLD_LEN]], 
                'size': row[fields[CRH_FLD_STO]]
            }        
            
            # create the reach and keep track of downstream reach and catchment
            reach = Reach(reachBarriers.get(oid, []), **attributes)
            reaches[oid] = (
                reach, row[fields[CRH_FLD_RDS]]
            )
            
            # record set of reaches for each catchment
            cid = row[fields[CRH_FLD_CAT]]
            if cid not in catchmentReaches:
                catchmentReaches[cid] = []
            catchmentReaches[cid].append(reach)
            
            # record set of reaches for each tributary
            tid = row[fields[CRH_FLD_TID]]
            if tid not in tributaryReaches:
                tributaryReaches[tid] = []
            tributaryReaches[tid].append(reach)
            
        # set reach downstream reaches
        for oid in reaches:
            if reaches[oid][1] is None: reaches[oid][0].down = reaches[oid][0]
            else: reaches[oid][0].down = reaches[reaches[oid][1]][0]
        
        
        # ~~ CREATE CATCHMENTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # create catchments that contain reaches
        fields, table = data[CRH_DAT_CAT]
        catchments = {}
        for row in table:
            
            # define basic attributes
            oid = row[fields[CRH_FLD_CAT]]
            attributes = {'id': oid, 'area': row[fields[CRH_FLD_WSA]]}
            
            # create the catchment and keep track of downstream catchment
            catchment = Catchment(catchmentReaches.get(oid, []), **attributes)
            catchments[oid] = (
                catchment, row[fields[CRH_FLD_CDS]]
            )
            
        # set catchment downstream catchments
        for oid in catchments:
            if catchments[oid][1] is None: catchments[oid][0].down = catchments[oid][0]
            else: catchments[oid][0].down = catchments[catchments[oid][1]][0]
        
        
        # ~~ CREATE TRIBUTARIES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # create tributaries that contain reaches and catchments
        fields, table = data[CRH_DAT_TRB]
        tributaries = {}
        lakeTributaries = {}
        for row in table:
            
            # define basic attributes
            oid = row[fields[CRH_FLD_TID]]
            attributes = {'id': oid}
            
            # create the tribuary and keep track of lake
            tributary = Tributary(tributaryReaches.get(oid, []), **attributes)
            tributaries[oid] = tributary
            
            # record set of tributaries for each lake
            lid = row[fields[CRH_FLD_LAK]]
            if lid not in lakeTributaries:
                lakeTributaries[lid] = []
            lakeTributaries[lid].append(tributary)
            
            
        # ~~ CREATE LAKES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # create lakes that contain tributaries
        lakes = [Lake(lakeTributaries[lakeID], id=lakeID) for lakeID in lakeTributaries]
        
        
        # ~~ CREATE HYDROGRAPHY ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        # create hydrography that contains everything
        self.lakes = lakes
        
        # add warning about lost catchments
        catCount = 0
        for lake in lakes:
            for tributary in lake.tributaries:
                catCount += len(tributary.catchments)
                
        diff = len(data[CRH_DAT_CAT][1]) - catCount
        if diff > 0:
            print 'WARNING: Automatically discarded %i catchments with no associated reaches.' % diff
        
        
    def get_objects(self, objType):
        """Returns all objects of a given class in the Hydrography network."""
        objects = set()
        
        # return Lakes
        if objType is Lake:
            objects.update(self.lakes)
            
        # loop through Lakes to get return objects
        else:
            for lake in self.lakes:
            
                # return Tributaries
                if objType is Tributary:
                    objects.update(lake.tributaries)
                    
                # loop through Tributaries to get return objects
                else:
                    for tributary in lake.tributaries:
                        
                        # return reaches
                        if objType is Reach:
                            objects.update(tributary.reaches)
                            
                        # return catchments
                        elif objType is Catchment:
                            objects.update(tributary.catchments)
                            
                        # loop through reaches to get barriers
                        else:
                            for reach in tributary.reaches:
                            
                                # return barriers
                                if objType is Barrier:
                                    objects.update(reach.barriers)
                                    
                                # unknown type
                                else:
                                    raise TypeError('Unknown return type: %s' % objType.__class__.__name__)
        
        return objects
        
    
    def get_barriers(self):
        """Returns a set of all barriers in the Hydrography network."""
        return self.get_objects(Barrier)


    def get_reaches(self):
        """Returns a set of all reaches in the Hydrography network."""
        return self.get_objects(Reach)
        
        
    def get_catchments(self):
        """Returns a set of all catchments in the Hydrography network."""
        return self.get_objects(Catchment)    
        
        
    def get_tributaries(self):
        """Returns a set of all reaches in the Hydrography network."""
        return self.get_objects(Tributary)

        
    def get_lakes(self):
        """Returns a set of all Lakes in the Hydrography network."""
        return self.get_objects(Lake)
        
        
if __name__ == '__main__':

    from __test__ import __test__
    from load_data import load_hydro_mdb
    __test__()
    
    database = r'C:\Users\Austin\Dropbox\UW Madison Post Doc\Data(Temp)\Barriers\hydro_update\GL_pruned_hydrography.mdb'
    data = load_hydro_mdb(database)
    hydrography = Hydrography(data)
    
    print 'Total lakes: %i' % len(hydrography.get_lakes())
    print 'Total catchments: %i' % len(hydrography.get_catchments())
    print 'Total tributaries: %i' % len(hydrography.get_tributaries())
    print 'Total reaches: %i' % len(hydrography.get_reaches())
    print 'Total barriers: %i' % len(hydrography.get_barriers())
    
