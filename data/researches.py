theory = ['Josh Alman',
          'Alexandr Andoni',
          'Xi Chen',
          'Eleni Drinea',
          'Daniel Hsu',
          'Tal Malkin',
          'Christos Papadimitriou',
          'Toniann Pitassi',
          'Tim Roughgarden',
          'Rocco Servedio',
          'Clifford Stein',
          'Nakul Verma',
          'Mihalis Yannakakis',
          'Henry Yuen',
          'Timothy Randolph',
          'Timothy Roughgarden',
          'Robert Holliday',
          'Periklis Papakonstantinou',
          'Omri Weinstein',
          'Lior Horesh',
          'Alexei Ashikhmin',
          ]

graphics_ui = ['Lydia Chilton',
               'Steven Feiner',
               'Shree Nayar',
               'Brian Smith',
               'Changxi Zheng',
               'Christian Swinehart',
               'Michelle Levine',
               'Timothy Paine',
               'Celeste Layne',
               ]

nlp_speech = ['Daniel Bauer',
              'Julia Hirschberg',
              'Kathleen McKeown',
              'Zhou Yu',
              'Homayoon Beigi',
              'Michelle Levine',
              'Yassine Benajiba',
              'Smaranda Muresan',
              'Michael Collins',
              ]

security = ['Steven Bellovin',
            'Asaf Cidon',
            'Roxana Geambasu',
            'Suman Jana',
            'Gail Kaiser',
            'Tal Malkin',
            'Jason Nieh',
            'Baishakhi Rai',
            'Henning Schulzrinne',
            'Simha Sethumadhavan',
            'Jeannette Wing',
            'Junfeng Yang',
            'Michael Sikorski',
            'Michael Theobald',
            'Salvatore Stolfo',
            ]
          
bio = ['Andrew Blumberg',
       'David Knowles',
       'Itsik Pe',
       'Kenneth Ross',
       'Ansaf Salleb-Aouissi',
       'Michael Theobald',
       'Yining Liu',
       ]

ss = ['Paul Blaer',
      'Luca Carloni',
      'Asaf Cidon',
      'Roxana Geambasu',
      'Luis Gravano',
      'Ronghui Gu',
      'Suman Jana',
      'Gail Kaiser',
      'Martha Kim',
      'Jason Nieh',
      'Baishakhi Ray',
      'Kenneth Ross',
      'Dan Rubenstein',
      'Bjarne Stroustrup',
      'Jeannette Wing',
      'Eugene Wu',
      'Junfeng Yang',
      'Alexandros Biliris',
      'Donald Ferguson',
      'Yongwhan Lim',
      'Sambit Sahu',
      ]

ce = ['Luca Carloni',
      'Stephen Edwards',
      'Martha Kim',
      'Jason Nieh',
      'Simha Sethumadhavan',
      'Kenneth Shepard',
      'Xiaofan Jiang',
      'Mingoo Seok',
      ]

net = ['Augustin Chaintreau',
       'Jae Woo Lee',
       'Vishal Misra',
       'Dan Rubenstein',
       'Henning Schulzrinne',
       'Gil Zussman',
       'Ethan Katz-Bassett',
       'Zoran Kostic',
       'Predrag Jelenkovic',
       'Ching-Yung Lin',
       'Alexei Ashikhmin',
       ]

vr = ['Peter Belhumeur',
      'Shih-Fu Chang',
      'Tony Dear',
      'John Kender',
      'Shree Nayar',
      'Brian Smith',
      'Shuran Song',
      'Carl Vondrick',
      'Changxi Zheng',
      'Peter Allen',
      ]

ml = ['Akshay Hall-Krishnamurthy',
      'Alexandr Andoni',
      'Salvatore Stolfo',
      'Adam Kelleher',
      'John Paisley',
      'Periklis Papakonstantinou',
      'Elias Bareinboim',
      'David Blei',
      'Adam Cannon',
      'Shih-Fu Chang',
      'Tony Dear',
      'Daniel Hsu',
      'David Knowles',
      'Toniann Pitassi',
      'Ansaf Salleb-Aouissi',
      'Shuran Song',
      'Nakul Verma',
      'Carl Vondrick',
      'Richard Zemel',
      'Alp Kucukelbir',
      'Bryan Gibson',
      'Homayoon Beigi',
      'Iddo Drori',
      'Joshua Gordon',
      'Timothy Paine',
      'Parijat Dube',
      'Vijay Pappu',
      'Yassine Benajiba',
      'Antonio Moretti',
      ]

ai = ['Elias Bareinboim',
      'Antonio Moretti',
      'Daniel Bauer',
      'Yassine Benajiba',
      'Peter Belhumeur',
      'David Blei',
      'Shih-Fu Chang',
      'Julia Hirschberg',
      'Daniel Hsu',
      'John Kender',
      'Kathleen McKeown',
      'Shree Nayar',
      'Ansaf Salleb Aouissi',
      'Brian Smith',
      'Shuran Song',
      'Nakul Verma',
      'Carl Vondrick'
      ]

fp = open("faculty.txt")
for line in fp:
    fields = line.split("'")
    uni = fields[1]
    name = fields[3]
    if name in theory:
        print("INSERT INTO RESEARCHES VALUES ('"+uni+"', 'Theory');")
    if name in graphics_ui:
        print("INSERT INTO RESEARCHES VALUES ('"+uni+"', 'Graphics and User Interfaces');")
    if name in nlp_speech:
        print("INSERT INTO RESEARCHES VALUES ('"+uni+"', 'Natural Language Processing and Speech');")
    if name in security:
        print("INSERT INTO RESEARCHES VALUES ('"+uni+"', 'Security and Privacy');")
    if name in bio:
        print("INSERT INTO RESEARCHES VALUES ('"+uni+"', 'Computational Biology');")
    if name in ss:
        print("INSERT INTO RESEARCHES VALUES ('"+uni+"', 'Software Systems');")
    if name in ce:
        print("INSERT INTO RESEARCHES VALUES ('"+uni+"', 'Computer Engineering');")
    if name in net:
        print("INSERT INTO RESEARCHES VALUES ('"+uni+"', 'Networking');")
    if name in vr:
        print("INSERT INTO RESEARCHES VALUES ('"+uni+"', 'Vision and Robotics');")
    if name in ml:
        print("INSERT INTO RESEARCHES VALUES ('"+uni+"', 'Machine Learning');")
    if name in ai:
        print("INSERT INTO RESEARCHES VALUES ('"+uni+"', 'Artificial Intelligence');")
