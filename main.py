from bs4 import BeautifulSoup
import bs4
from requests import get
import sqlite3


db = sqlite3.connect('dane.db')

cursor = db.cursor()

cursor.execute("""select l.id, l.name, l.link
                    from league l
                    where l.id not in (select t.league_id  from team t join player p on p.team_id = t.id)""")
leagues_to_parse = cursor.fetchall()

for league in leagues_to_parse:

    print(league)

    url = league[2]

    page = get(url)

    bs = BeautifulSoup(page.content, 'lxml')

    club_list = {}
    for row in bs.find_all('span', class_='name'):
        club_list.update({row.string:row.parent.attrs['href'].split('/')[-1].split('.')[0]})

    for key, value in club_list.items():
        print(key)
        i=0
        player_list = []
        cursor.execute("SELECT id FROM team where link=?", (value,))
        id_team = cursor.fetchone()

        if not id_team:
            id_team = cursor.execute("""INSERT INTO team (name,link,league_id)
            VALUES(?,?,?)""", (key,value,league[0]))
            db.commit()
            cursor.execute("SELECT id FROM team where link=?", (value,))
            id_team = cursor.fetchone()

        id_team = id_team[0]
        page = get('https://www2.laczynaspilka.pl/druzyna-szczegoly-sezon/'+ value + ',2021-2022.html')
        bs_club = BeautifulSoup(page.content, 'lxml')
        for player in  bs_club.find('table',class_='table-template table-season-pro pro--labels').tbody.find_all('tr',class_='player-row'):
            surname = player.td.find('span',class_='surname').string
            name = player.td.find('span',class_='name').string
            link = player.td.find('a').attrs['href']
            player_list.append([link,surname,name])

        for player in bs_club.find('table', class_='table-template table-season-pro pro--views js__fixed-header table-header-sticky__content').tbody.find_all('tr',class_='player-row'):
            if len(player_list)>i:
                score_total_for_player = len(player.find_all('i',class_='i-goal-small'))
                yellow_card_total_for_player = len(player.find_all('i',class_='i-card-yellow card--small'))
                red_card_total_for_player = len(player.find_all('i',class_='i-card-red card--small'))
                cursor.execute("SELECT id FROM player where link=?", (player_list[i][0],))
                id_player = cursor.fetchone()
                if id_player:
                    cursor.execute("""  UPDATE player
                                        SET surname = ?,
                                        name =?,
                                        link =?,
                                        team_id =?,
                                        goals_sum =?,
                                        yellow_cards_sum =?,
                                        red_cards_sum =?
                                        WHERE
                                        id = ?""", (player_list[i][1],player_list[i][2],player_list[i][0],id_team,score_total_for_player,yellow_card_total_for_player,red_card_total_for_player,id_player[0]))
                else:
                    cursor.execute("""INSERT INTO player (surname,name,link,team_id,goals_sum,yellow_cards_sum,red_cards_sum)
                    VALUES(?,?,?,?,?,?,?)""", (player_list[i][1],player_list[i][2],player_list[i][0],id_team,score_total_for_player,yellow_card_total_for_player,red_card_total_for_player))
                
                db.commit()
            i=i+1
