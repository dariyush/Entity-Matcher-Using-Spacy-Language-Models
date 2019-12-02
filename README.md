# Entity Matcher Using Language Models

# Installation:
Open a command window prompt in administrator mode. Then;

	- cd path_to_the_directory_which_includes_setup.py
	
	- pip install . --user
	
	
# Examples:
	from NLP import GetNLP
    nlp = GetNLP(units=True, ame=True)
    
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
	
	Comp = nlp.get_pipe('Component')
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
