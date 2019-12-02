# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 10:17:41 2018

@author: a.mohammadi
"""

import pyodbc

from spacy.tokens import Doc, Span, Token
from spacy import load

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from pandas import read_sql

from spacy.matcher import Matcher
from spacy.attrs import LOWER

from re import findall as reFindall, compile as reCompile
from re import IGNORECASE as reIGNORECASE, sub as reSub, match as reMatch

#%%
def connectionParams(server, database):
    return ''.join([r'DRIVER={ODBC Driver 13 for SQL Server};',
                    r'Trusted_Connection=yes;',
                    r'SERVER=%s;' %server, 
                    r'DATABASE=%s;' %database,])
     


#%%
class Component(object): # self=Component()
    name = 'Component'
   
    def __init__(self, countriesIDNm, commoditiesIDNm, 
                 commoditiesIDCode, sitesIDNm, companiesIDNm):
        
        ########## countries
        self.countriesIDNm = countriesIDNm
        ctrPat = ''    
        for ctrid, anl in self.countriesIDNm.items():
            anlpat = '\W|\W'.join(anl)
            ctrPat = ctrPat + f"|(?P<c{ctrid}>\\W{anlpat}\\W)" 
        ctrPat = ctrPat.strip('|')
        
        self.ctrPatCompiled = reCompile( ctrPat )
        Span.set_extension('countries', getter=self.Countries, force=True)
        Doc.set_extension('countries', default=None, force=True)

        ########## Commodities
        self.commoditiesIDNm = commoditiesIDNm
        self.commoditiesIDCode = commoditiesIDCode     
        comPat = ''    
        for commid, names in self.commoditiesIDNm.items():
            namespat = '\W|\W'.join(names)
            comPat = comPat + f"|(?P<com{commid}>\\W{namespat}\\W)" 
        comPat = comPat.strip('|')
        
        comCodePat = ''    
        for commid, commcode in self.commoditiesIDCode.items():
            comCodePat = comCodePat + f"|(?P<com{commid}>\\W{commcode}\\W)" 
        comCodePat = comCodePat.strip('|')   

        self.comCodePatCompiled = reCompile(comCodePat)
        self.comPatCompiled = reCompile(comPat, reIGNORECASE)
        Span.set_extension('commodities', getter=self.Commodities, force=True)
        Doc.set_extension('commodities', default=None, force=True)
        
        ########## sites
        self.sitesIDNm = sitesIDNm
        self.siteNms = list( self.sitesIDNm.values() )
        self.siteIDs = list( self.sitesIDNm.keys() )
        
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2,5), 
                             encoding='utf-8-sig', lowercase=False )
        self.modelChar = vectorizer.fit( self.siteNms )
        vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1,4), 
                             encoding='utf-8-sig', lowercase=False )
        self.modelWord = vectorizer.fit( self.siteNms )
        self.sitesTFChar = self.modelChar.transform( self.siteNms )
        self.sitesTFWord = self.modelWord.transform( self.siteNms )
        
        Span.set_extension('sites', getter=self.Sites, force=True)
        Doc.set_extension('sites', default=None, force=True)
        
        ########## companies
        self.companiesIDNm = companiesIDNm
        self.companiesNm = list( self.companiesIDNm.values() )
        self.companiesID = list( self.companiesIDNm.keys() )

        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2,5), 
                                     encoding='utf-8-sig', lowercase=False )
        self.modelCharCompanies = vectorizer.fit( self.companiesNm )
        vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1,4), 
                                     encoding='utf-8-sig', lowercase=False )
        self.modelWordCompanies = vectorizer.fit( self.companiesNm )
        self.CompaniesTFChar = self.modelCharCompanies.transform( self.companiesNm )
        self.CompaniesTFWord = self.modelWordCompanies.transform( self.companiesNm )
        
        Span.set_extension('companies', getter=self.Companies, force=True)
        Doc.set_extension('companies', default=None, force=True)
        
        ##########
    def Companies(self, span):
        text = [' '+span.text+' ',]
        ncTF = self.modelWordCompanies.transform( text )
        cossim = cosine_similarity(self.CompaniesTFWord, ncTF)
        simsWord = cossim.max()
        argsWord = cossim.argmax()
        
        ncTF = self.modelCharCompanies.transform( [span.text,] )
        cossim = cosine_similarity(self.CompaniesTFChar, ncTF)
        simsChar = cossim.max()
        argsChar = cossim.argmax()
        sim = simsWord * simsChar
        
        if sim < 0.4:
            return []
        if simsWord >= simsChar:
            args = argsWord
        elif simsChar >= simsWord:
            args = argsChar
        else:
            return None
            
        cid = self.companiesID[ args ]
#        cnm = self.companiesNm[ args ]
        return [cid,]
    
    def Sites(self, span):
        text = [' '+span.text+' ',]
        ncTF = self.modelWord.transform( text )
        cossim = cosine_similarity(self.sitesTFWord, ncTF)
        simsWord = cossim.max()
        argsWord = cossim.argmax()
        
        ncTF = self.modelChar.transform( [span.text,] )
        cossim = cosine_similarity(self.sitesTFChar, ncTF)
        simsChar = cossim.max()
        argsChar = cossim.argmax()
        sim = simsWord * simsChar
        
        if sim < 0.4:
            return []
        if simsWord >= simsChar:
            args = argsWord
        elif simsChar >= simsWord:
            args = argsChar
        else:
            return None
            
        sid = self.siteIDs[ args ]
#        snm = self.siteNms[ args ]
        return [sid,]

    def Commodities(self, span):
        string = ' ' + span.text + ' ' 
        commodities = []
        for match in self.comPatCompiled.finditer( string ):
            commodities.append( int( match.lastgroup[3:] ) )
        for match in self.comCodePatCompiled.finditer( string ):
            commodities.append( int( match.lastgroup[3:] ) )
        return commodities

    def Countries(self, span):
        string = ' ' + span.text + ' '        
        coutries = []
        for match in self.ctrPatCompiled.finditer( string ):
            coutries.append( int( match.lastgroup[1:] ) )
        return coutries
       
    def GetSpans(self, doc):
        if not len(doc):
            return []
        #for tok in doc: print(tok, tok.dep_, tok.pos_, tok.like_num, tok.lemma_, tok.shape_)

        chunks = list(doc.noun_chunks) + list(doc.ents) 
        for tok in doc: 
            if tok.like_num or tok.shape_.lower() in ['ddddxd', 'ddddxd', 'xxddxd']: 
#           tok.pos_ in ['PROPN']:
                chunks.append( Span(doc, tok.i, tok.i+1) )

        nces = sorted([ [nc.start, nc.end, nc] 
                        for nc in chunks if nc.text.strip() ])    
        if not len(nces):    
            return [Span(doc, 0, len(doc)),]
        
        spans = []
        start, end, span = nces[0]
        for start, end, nc in nces:        
            if span.end < start:
                spans.append(span)
                span = nc
            else:
                span = Span(doc, min(span.start, start), max(span.end, end) )
        if span not in spans:
            spans.append(span)   
        
        return spans

    def __call__(self, doc):
        doc.user_data['spans'] = self.GetSpans(doc)
        countries, sites, commodities, companies = ([] for i in range(4))
        for span in doc.user_data['spans']:
#            span = doc.user_data['spans'][9]
            countries.extend(span._.countries)
            sites.extend(span._.sites)
            commodities.extend(span._.commodities)
            companies.extend(span._.companies)
            
        doc._.countries = countries
        doc._.sites = sites
        doc._.commodities = commodities
        doc._.companies = companies
       
        return doc  

#%%
class UnitComponent(object):     # self = UnitComponent()
    name = 'UnitComponent' 
    def hasUnit(self, tokens):
        return any([tok._.get('hasUnit') for tok in tokens])
    
    def __init__(self, nlp, units={}, label='UNIT', debug=0):
        self.debug = debug
        
#        currencies = '\$|US\$|US¢|¢|£|€|¥|฿|C\\$|A\\$|₽|﷼|Dollars?|NZ\$'
#        patCUR = reCompile(currencies, re.I)
        
        currencies = "\$|\$MN|\$U|\$b|\.د\.ب|\.ރ|/-|/="\
        +"|A\$|AED|AFN|ALL|AMD|AOA|ARS|AUD|AWG|AZN|Afl|Afs|A﹩|A＄"\
        +"|B\$|B/\.|BAM|BBD|BDT|BGN|BHD|BIF|BMD|BND|BOB|BRL|BSD|BTN|BWP|BYN"\
        +"|BZ\$|BZD|BZ﹩|BZ＄|Bds\$|Bds﹩|Bds＄|Bs\.|Bs\.F\.|B﹩|B＄"\
        +"|C\$|CA\$|CAD|CA﹩|CA＄|CDF|CFP|CHF|CI\$|CI﹩|CI＄|CLP|CLP\$|CLP﹩"\
        +"|CLP＄|CNY|CN¥|CN￥|COP|CRC|CUP|CVE|CZK|C﹩|C＄|DJF|DKK|DOP|DZD|Dhs"\
        +"|Dollar|Dollars|EC\$|EC﹩|EC＄|EGP|ERN|ETB|EUR|E£|E￡|FJ\$|FJD|FJ﹩"\
        +"|FJ＄|FRw|Fr\.|Franc|Francs|G\$|GBP|GB£|GB￡|GEL|GFr\.|GHS|GH¢|GH₵"\
        +"|GMD|GNF|GTQ|GY\$|GYD|GY﹩|GY＄|G﹩|G＄|HK\$|HKD|HK﹩|HK＄|HNL|HRK|HTG"\
        +"|HUF|IDR|ILS|INR|IQD|IRR|ISK|J\$|JMD|JOD|JPY|JP¥|JP￥|J﹩|J＄|KES|KGS"\
        +"|KHR|KMF|KPW|KRW|KWD|KYD|KZT|L\$|L\.E\.|LAK|LBP|LD\$|LD﹩|LD＄|LKR|LRD"\
        +"|LSL|LYD|Lekë|L﹩|L＄|MAD|MDL|MGA|MKD|MMK|MNT|MOP|MOP\$|MOP﹩|MOP＄|MRO"\
        +"|MRf|MUR|MVR|MWK|MX\$|MXN|MX﹩|MX＄|MYR|MZN|Mex\$|Mex﹩|Mex＄|N\$|NAD|NGN"\
        +"|NIO|NIS|NOK|NPR|NT\$|NT﹩|NT＄|NZ\$|NZD|NZ﹩|NZ＄|Nu\.|N﹩|N＄"\
        +"|OMR|PAB|PEN|PGK|PHP|PKR|PLN|PYG|Pound|Pounds|QAR|R\$|RD\$|RD﹩"\
        +"|RD＄|RMB|RON|RSD|RUB|RWF|R₣|R﹩|R＄|S\$|S/|S/\.|SAR|SAT|SBD|SCR|SDG"\
        +"|SEK|SFr\.|SGD|SI\$|SI﹩|SI＄|SLL|SLRs|SOS|SRD|SSP|STD|SVC|SYP|SZL"\
        +"|Sh\.So\.|Shilling|Shillings|S£|S﹩|S＄|S￡|T\$|THB|TJS|TMT|TND|TOP"\
        +"|TRY|TT\$|TTD|TT﹩|TT＄|TWD|TZS|T﹩|T＄|UAH|UGX|UKP|US\$|USD|US﹩|US＄"\
        +"|UYU|UZS|VEF|VND|VUV|WS\$|WST|WS﹩|WS＄|XAF|XCD|XOF|XPF|YER|Z\$|ZAR"\
        +"|ZMW|ZWL|Z﹩|Z＄|balboa|balboas|birr|colones|colón|darahim|den|denari"\
        +"|din|dinar|dinars|dirhams|dobra|dobras|dollar|dollars|dong|dram"\
        +"|euro|euros|franc|francs|goud|gourde|gourdes|guaraní|guaraníes|kall"\
        +"|kina|kip|kr\.|krónur|kwacha|lari|lek|leone|leones|leu|lev|m\.|man\.|manat"\
        +"|meticais|metical|naira|ouguiya|rand|rial|rials|riel|riels"\
        +"|riyal|riyals|rupee|rupees|shilingi|shilling|shillings|sol|soles|tenge"\
        +"|tögrög|¢|£|£E|£S|¥|Íkr|đồng|лв\.|ман|руб"\
        +"|сўм|֏|ש\"ח|؋|ج\.س|ج\.م|د\.إ|د\.ت|د\.ع|د\.ك|ر\.س|ر\.ق|ش\.ج|ل\.د|ل\.ل\.‎|ناكفا|रु"\
        +"|৳|ரூ|රු|฿|ናቕፋ|៛|₡|₦|₨|₩|₪|₫|€|₭|₭N|₮|₱|₲|₴|₵|₸|₹|₺|₼|₽|₾|﷼|﹩|﹩MN"\
        +"|﹩U|﹩b|＄|＄MN|＄U|＄b|￡|￡E|￡S|￥|￦"
  
        patCUR = reCompile('('+currencies+')$')
        FuncCUR = lambda text: any( [True for t in text.split('/') if patCUR.match(t)] )
        self.IS_CURR = nlp.vocab.add_flag( FuncCUR )   
        
        # matcher level case sensetive: in, t, d, m, s, y, J, K, L, ac, rod, bar
        units = { #token level; No space patterns 
        'Length': 'foot|feet|ft|inche?s?|metres?|kilometres?'\
                    +'|thou|mil|miles?|mi|rd|yards?|yd|centimetres?'\
                    +'|micrometres?|microns?|μ|μm|nanometres?|nm|nmi|parsec|picometres?',
        'Area': 'hectares?|ha|km2|m2|acre',
        'Mass': 'carats?|ct|kg|kt|kip|oz|troy|ounces?|pounds?|lb|tons?|tonnes?|hundredweight|cwt|quintal',
        'Volume': 'barrels?|bbl|bl|bucket|bkt|bushel|bu|cf|ft3|in3|m3|yd3'\
                     +'|gal|litres?|gallons?|quart|qt',
                             
        'Time': 'days?|decades?|dec|fortnights?|fn|hours?|h|minutes?|min|monthe?s?|mo'\
                +'|seconds?|sec|weeks?|wk|years?|yr|annum',
        'Speed': 'knot|kn|rpm|fph|fpm|fps|iph|ipm|ips|mph|mpm|mps',
        'Flow': 'cfm|GPD|GPH|GPM|LPM',
        
        'Force': 'newton|N|poundal|pdl|lbf|ozf|tnf|kgf|kp|Gf|kip|kipf|klbf',
        'Pressure': 'pascal|Pa|atm|atmosphere|cmHg|cmH2O|ftHg|ftH2O|inHginH2O|pz|psf|psi|torr',
        'Energy': 'boe|BTU|Calorie|Cal|CHUIT|hp·h|joule|tTNT|toe|TCE',
        'Power': 'horsepower|hp|watt',
        'Temperature': 'Celsius|°C|Fahrenheit|°F|kelvin|°K',
        'Percent': 'cent|percent',
        'Mult': 'millions?|nauticals?|thousands?|billions?|[’‘]?000',
        'MultArea': 'square|sq',
        'MultVolume': 'cu|cubic|fl',
         }

        patMAS = reCompile('([bkm]{0,2})('+units["Mass"]+')$', reIGNORECASE)
        FuncMAS = lambda text: any([True if patMAS.match(t) else False for t in text.split('/')] )
        
        patVOL = reCompile('([bkm]{0,2})('+units["Volume"]+')$', reIGNORECASE)
        FuncVOL = lambda text: any([True if patVOL.match(t) else False for t in text.split('/')] ) 
    
        patLEN = reCompile('([bkm]{0,2})('+units["Length"]+')$', reIGNORECASE)
        FuncLEN = lambda text: any([True if patLEN.match(t) else False for t in text.split('/')] )
    
        patARE = reCompile('([bkm]{0,2})('+units["Area"]+')$', reIGNORECASE)
        FuncARE = lambda text: any([True if patARE.match(t) else False for t in text.split('/')] )
    
        patMUL = reCompile('\W('+units["Mult"]+')\W', reIGNORECASE)
        FuncMUL = lambda text: any([True if patMUL.match(' '+t+' ') else False for t in text.split('/')] )
    
        patMUA = reCompile('('+units["MultArea"]+')$', reIGNORECASE)
        FuncMUA = lambda text: any([True if patMUA.match(t) else False for t in text.split('/')] )
    
        patMUV = reCompile('('+units["MultVolume"]+')$', reIGNORECASE)
        FuncMUV = lambda text: any([True if patMUV.match(t) else False for t in text.split('/')] )
        
        patCEN = reCompile('('+units["Percent"]+')$', reIGNORECASE)
        FuncCEN = lambda text: bool( patCEN.search(text) )
        
        patTIM = reCompile('('+units["Time"]+')$', reIGNORECASE)
        FuncTIM = lambda text: any([True if patTIM.match(t) else False for t in text.split('/')] )
        
        patSPE = reCompile('('+units["Speed"]+')$', reIGNORECASE)
        FuncSPE = lambda text: any([True if patSPE.match(t) else False for t in text.split('/')] )
        
        patFLO = reCompile('('+units["Flow"]+')$', reIGNORECASE)
        FuncFLO = lambda text: any([True if patFLO.match(t) else False for t in text.split('/')] )
        
        patPRE = reCompile('('+units["Pressure"]+')$', reIGNORECASE)
        FuncPRE = lambda text: any([True if patPRE.match(t) else False for t in text.split('/')] )
        
        patENE = reCompile('('+units["Energy"]+')$', reIGNORECASE)
        FuncENE = lambda text: any([True if patENE.match(t) else False for t in text.split('/')] )
        
        patPOW = reCompile('('+units["Power"]+')$', reIGNORECASE)
        FuncPOW = lambda text: any([True if patPOW.match(t) else False for t in text.split('/')] )
        
        patTEM = reCompile('('+units["Temperature"]+')$', reIGNORECASE)
        FuncTEM = lambda text: any([True if patTEM.match(t) else False for t in text.split('/')] )
        
        self.unitTuples = [('MAS', FuncMAS), ('VOL', FuncVOL),
                           ('LEN', FuncLEN), ('ARE', FuncARE),  
                           ('MUA', FuncMUA), ('MUV', FuncMUV), ('MUL', FuncMUL),
                           ('ENE', FuncENE), ('POW', FuncPOW),
                           
                            #('CEN', FuncCEN), ('TIM', FuncTIM), ('PRE', FuncPRE),
                            #('SPE', FuncSPE), ('TEM', FuncTEM), ('FLO', FuncFLO), 
                          ]
    
        def FuncUNIT(text):
            for _, f in self.unitTuples: 
                if f(text):
                    return True
            return False
        self.IS_UNIT = nlp.vocab.add_flag( FuncUNIT )    

        Token.set_extension('ut', default=[], force=True)
        Token.set_extension('hasUnit', default=False, force=True)
        Span.set_extension('hasUnit', getter=self.hasUnit, force=True)
        Doc.set_extension('units', default=None, force=True)
        Doc.set_extension('unitTypes', default=None, force=True)
        
        # matcher 
        self.matcher = Matcher(nlp.vocab)
        # Currency match rules
        self.matcher.add('curr', None, [{self.IS_CURR: True, 'OP': '+'}])
        self.matcher.add('curr', None, [{self.IS_CURR:True}, {LOWER: '/'}, {}])
        self.matcher.add('curr', None, [{}, {LOWER: '/'}, {self.IS_CURR:True}])
        
        # Unit match rules
        self.matcher.add('unit', None, [{self.IS_UNIT: True, 'OP': '+'}])
        self.matcher.add('unit', None, [{self.IS_UNIT:True}, {LOWER: '/'}, {}])
        self.matcher.add('unit', None, [{}, {LOWER: '/'}, {self.IS_UNIT:True}])
        self.matcher.add('unit', None, [{self.IS_UNIT:True}, {LOWER: 'of'}, {self.IS_UNIT:True}])
            
        # Currency and Unit match reules    
        self.matcher.add('currunit', None, [{self.IS_CURR: True}, 
                         {'LIKE_NUM': True, 'OP': '*'}, {self.IS_UNIT: True}])
        self.matcher.add('unit', None, [{self.IS_UNIT:True}, {LOWER: 'of'}, {self.IS_CURR:True}])

        # Other match rules        
        self.matcher.add('curr', None, [{}, {LOWER: 'per'}, {}])
        self.matcher.add('unit', None, [{self.IS_UNIT: True}, {LOWER: 'a'}, {}])
        self.matcher.add('curr', None, [{'LIKE_NUM': True, 'OP': '*'}, {LOWER:'m'}])
        self.matcher.add('others', None, [{self.IS_UNIT: True}, {LOWER: 'of', 'OP': '?'}, 
                                        {LOWER: 'oil'}, {LOWER: 'equivalent'}])
       
    def __call__(self, doc):
#        if self.debug:
#            print(doc)
            
        for tok in doc:
            if tok.check_flag( self.IS_UNIT ): 
                tok._.hasUnit = True
                tok._.ut = [utype for utype, ufunc in self.unitTuples 
                                    if ufunc(tok.text)]
            if tok.check_flag( self.IS_CURR ):
                tok._.hasUnit = True
                tok._.ut = tok._.ut + ['CUR']

#        if self.debug:
#            print('\n')
#            for tok in doc: print(tok, tok._.ut, tok._.hasUnit, tok.like_num )
        
        matches = self.matcher(doc)
        spans, uts = [], []
        span = None
        for match_id, start, end in matches:        
            if span and start <= span.end:
                span = Span(doc, span.start, end)
                ut = [utype for tok in span for utype in tok._.ut]
                spans[-1] = span
                uts[-1] = ut
            else:
                span = Span(doc, start, end)
                ut = [utype for tok in span for utype in tok._.ut]
                spans.append(span)
                uts.append(ut)
            
#        if self.debug:
#            print('\nMatched Spans:', )
#            for span in spans: print([t for t in span])
    
        for span, ut in zip(spans, uts):
            span.merge()
            for span, ut in zip(spans, uts):
                span.merge()
                
                if len(ut)==0 \
                or ( len(ut)==1 and ut[0] in ['DIV', 'MUV', 'MUA', 'MUL'] ):
                    span[0]._.ut = []
                    span[0]._.hasUnit = False
                                            
                else:
                    span[0]._.ut = ut
                    span[0]._.hasUnit = True
        
        utexts = [tok.text for tok in doc if tok._.hasUnit]
        doc._.units = [reSub(' \d|[\d\.,]+', '', text) 
                    if not reMatch("[’‘]?000", text) else text
                    for text in utexts ]
        doc._.unitTypes = [' '.join(tok._.ut) for tok in doc if tok._.hasUnit ]
        
#        if self.debug:
#            print('\n')
#            for tok in doc: print(tok, tok._.hasUnit, tok._.ut, tok.ent_type_ )   
        
        return doc
#%%
def GetNLP(countriesIDNm, commoditiesIDNm, commoditiesIDCode, 
           sitesIDNm, companiesIDNm ):
    
    nlp = load('en_core_web_sm') 
    
    Comp = Component(countriesIDNm, commoditiesIDNm, 
                 commoditiesIDCode, sitesIDNm, companiesIDNm)
    nlp.add_pipe( Comp ) 
        
    UnitComp = UnitComponent(nlp)
    nlp.add_pipe( UnitComp )
    
    return nlp
    
#%%
if __name__=="__main__":
    
    nlp = GetNLP(countriesIDNm = countriesIDNm, 
                 commoditiesIDNm = commoditiesIDNm,
                 commoditiesIDCode = commoditiesIDCode, 
                 sitesIDNm = sitesIDNm, 
                 companiesIDNm = companiesIDNm)
    
    Comp = nlp.get_pipe('Component')
    
    text = ' ' + """Hartley platinum project, Zimbabwe; Hot Briquetted Iron plant, 
              Yandi iron ore mine expansion and Beenup titanium minerals project, 
              Western Australia; Cannington silver, lead, zinc project and 
              Crinum coking coal mine, Queensland, Australia; 
              Mt Owen thermal coal development, New South Wales, Australia; 
              and Samarco pellet plant expansion, Brazil. 
              The Northwest Territories Diamonds project in Canada is subject to 
              a number of approvals. $41.669 million (1996 – $39.538 million).""" + ' '
              
    doc = nlp(text)

    print( doc.user_data, '\n')
    print( [Comp.countriesIDNm[ctrid] for ctrid in doc._.countries], '\n')
    print( [Comp.commoditiesIDNm[commid] for commid in doc._.commodities] , '\n')
    print( [Comp.sitesIDNm[sid] for sid in doc._.sites] , '\n')
    print( [Comp.companiesIDNm[cid] for cid in doc._.companies] , '\n')
    print( doc._.units, '\n', doc._.unitTypes , '\n')
    
    from re import split as resplit, search as reSearch
    for doc in nlp.pipe( resplit('\n|\t|\r\n', text) ):
        for tok in doc:
            if tok._.hasUnit:
                print(tok.text, reSearch(' \d|[\d\.,]+', tok.text).group(),
                      tok._.ut, tok.sent.text)

