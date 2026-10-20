# Verifiering — 2026-10-19

## Version 1.2.13 — tydligare mål- och budgetpanel, 2026-10-20

Minimivärdena ligger i höger kolumn direkt under modifierarlistan och hela modifierartexten. Modifierardetaljer och metadata ligger i samma kolumn. Flera minimivärden radbryts med två per rad. Vänster kolumn förklarar maxantal Chaos Orbs som den högsta tillåtna förbrukningen med automatiskt stopp vid gränsen eller tidigare vid träff. Shiftcheckbox och dess förklaring ligger under budgeten.

Mörka fältkanter med guldfärgat fokus, jämnare mellanrum, större standardhöjd och tre separata räknarkort förbättrar helheten. Språk, tillgänglighetskontroller, inställningar och körmotor behålls.

91 tester passerar, inklusive befintliga tester av språkbyte, flerradiga modifierare, egna mallar, stopp, budget och Shift (`artifacts/build-1.2.13.log`). Det paketerade röktestet passerar med två lika breda dropdowns på 450 pixlar (`artifacts/packaged-smoke-1.2.13.json`). Slutlig EXE har startats och båda språkens layout samt budget- och Shiftförklaringar har kontrollerats visuellt. Ingen Chaos användes.

## Version 1.2.12 — SVG som flaggkälla, 2026-10-20

Flaggorna genereras från `assets/se.svg` och `assets/us.svg` av `scripts/build_flags.py`. Byggsteget renderar i fyrdubbel upplösning med resvg och skalar ned med Lanczos till 32×20 respektive 38×20, centrerat på transparenta 38×24-ytor. Tkinter visar bilderna i exakt denna storlek utan uppförstoring. De gamla 16×12-bilderna används inte längre. SE/US och språk-ID:n behålls.

91 tester samt paketerat röktest passerar (`artifacts/build-1.2.12.log`, `artifacts/packaged-smoke-1.2.12.json`). Slutlig EXE har startats och båda flaggorna kontrollerats visuellt i språklistan. Ingen Chaos användes.

## Version 1.2.11 — egna flaggbilder, 2026-10-20

Språkväljaren använder nu de angivna filerna `assets/se.png` och `assets/us.png`, förstorade proportionellt från 16×12 till 32×24 pixlar. De tidigare ritade flaggorna är borttagna. Både knappen och menyn visar SE/US. Språkens interna ID:n och inställningar är oförändrade.

91 tester och det paketerade röktestet passerar (`artifacts/build-1.2.11.log`, `artifacts/packaged-smoke-1.2.11.json`). Den byggda versionen har startats och flaggbilderna samt SE/US har verifierats visuellt i den öppna språklistan. Ingen Chaos användes.

## Version 1.2.10 — flaggor och språkmeny, 2026-10-20

Språkväljaren visar ritade svenska och amerikanska flaggikoner samt SWE/USA. Rubriken till vänster växlar mellan SPRÅK och LANGUAGE. Menyn följer appens mörka färger och gulddetaljer, med tydlig markering vid hovring och tangentbordsfokus.

91 tester passerar (`artifacts/build-1.2.10.log`). Det nya GUI-testet kontrollerar flaggbilder, språkbyte med mus och tangentbord, bevarade arbetsdata och låsning under körning. Slutpaketeringen lyckades (`artifacts/package-1.2.10.log`). Det paketerade röktestet passerar och verifierar katalog, språkbyte, lika listbredder och Windowsikoner (`artifacts/packaged-smoke-1.2.10.json`).

Den färdiga EXE-filen har startats. Båda flaggorna, den öppna menyn, svenska SPRÅK/SWE och engelska LANGUAGE/USA har kontrollerats visuellt. Tidigare engelskt språkval har återställts. Ingen Chaos användes och craftingkedjan är oförändrad.

## Version 1.2.9 — engelska föremålsnamn och Windowsikon, 2026-10-20

Alla föremålstyper, attributvarianter och grupprubriker i föremålslistan visas nu på engelska i båda språklägena. Övrig svensk programtext är kvar. Språkbytestestet kontrollerar att listans innehåll, grupper och arbetsdata är oförändrade.

`assets/reroller_icon.png` används för Windowsikonen. Byggsteget skapar en proportionellt centrerad transparent ICO med nio storlekar (16–256 px) och bäddar in den i EXE-filen. Fönstret använder samma ICO, inklusive standardikon för dess popupfönster. Programmet har den uttryckliga Windowsidentiteten `Zyon.PoE2Reroller` för aktivitetsfältet. Skrivbordsgenvägen `PoE 2 Reroller.lnk` har skapats med programfilens ikon.

90 tester passerar. Det paketerade röktestet verifierar att både liten fönsterikon och stor aktivitetsfältsikon är registrerade hos Windows samt att appidentiteten stämmer (`artifacts/packaged-smoke-1.2.9.json`). `scripts/verify_packaged_icon.py` verifierar att alla nio inbäddade ikonbilder matchar ICO-filen och att Windows Shell lämnar rätt ikon för EXE och skrivbordsgenväg. Genvägens enda avvikelse är Windows pilöverlägg i nedre vänstra hörnet (`artifacts/icons-1.2.9.json`).

Visuellt verifierat: programfilens stora ikon i Utforskaren, R-ikonen i aktivitetsfältet och ikonen i appens övre vänstra hörn. Utforskarens gamla ikonvisning uppdaterades med F5 och stor ikonvy. Appen är startad i svenskt läge med engelska föremålsnamn. Ingen Chaos användes.

## Version 1.2.8 — kortkommandon och renare gränssnitt

En kompakt panel med tangentbrickor visar kalibrering (F6/F7), globalt nödstopp (F8/Shift+F8), kopiering i spelet (Ctrl+Alt+C), stängning/avbryt (Esc), listnavigering (pilar/Enter), fokus (Tab/Shift+Tab), aktivering (Space) och fönsterstängning (Alt+F4). Alt+Tab och dess stopp vid fokusförlust förklaras under listan. Panelen översätts med valt språk.

Extern katalogprofilering och webblänkar har tagits bort från gränssnittet, modifierardetaljerna, den paketerade katalogen, manifestet och levererad dokumentation. Modifierarvärden, tiers, stabila ID:n, matchning och craftingkedja är oförändrade. 90 tester och paketerat röktest passerar (`artifacts/build-1.2.8.log`, `artifacts/packaged-smoke-1.2.8.json`). Båda språklayouterna verifierades visuellt. Ingen Chaos användes.

## Version 1.2.7 — mörk Shift-stil

Shiftläget har en egen Checkbutton-stil med mörk hovringsbakgrund, ljus text, guldmarkering när det är valt och dämpad stil när kontrollen är låst. Den ljusa standardbakgrunden vid hovring används inte längre. 88 tester och paketerat röktest passerar (`artifacts/build-1.2.7.log`, `artifacts/packaged-smoke-1.2.7.json`). Vald och avmarkerad hovring verifierades visuellt i EXE-filen. Shiftläget återställdes till avmarkerat efter kontrollen. Ingen Chaos användes.

## Version 1.2.6 — bildhjälp för kalibrering

Länken `[SEE HOW]` / `[SE HUR]` ligger direkt efter kalibreringsinstruktionen och öppnar den inbäddade `assets/info.png` i en separat modal popup. Bilden visas i originalupplösning (828×832); rullningslister gör detaljerna åtkomliga på mindre skärmar. Popupen har ett stort rött kryss med Close/Stäng, ett vanligt fönsterkryss och Esc för stängning. Länken låses under körning. 88 tester och paketerat röktest passerar (`artifacts/build-1.2.6.log`, `artifacts/packaged-smoke-1.2.6.json`). GUI-testet kontrollerar båda språken, oförändrade arbetsdata och stängning med knapp respektive Esc. Länkens placering, bildens läsbarhet och stängknappen verifierades visuellt i EXE-filen. Ingen Chaos användes.

## Version 1.2.5 — halverad Reroller-bild

Reroller-bilden i sidhuvudet skalas nu till hälften av tidigare bredd och höjd. PoE 2-logotypen behåller sin storlek. 87 tester och paketerat röktest passerar (`artifacts/build-1.2.5.log`, `artifacts/packaged-smoke-1.2.5.json`). Storleken är visuellt verifierad i den startade EXE-filen.

## Version 1.2.4 — ny Reroller-bild

Sidhuvudet använder nu `assets/reroller.png` i stället för `chaos_reroller.png`, proportionellt skalad och inbäddad i EXE-filen. 87 tester och paketerat röktest passerar (`artifacts/build-1.2.4.log`, `artifacts/packaged-smoke-1.2.4.json`). Rätt bild, transparens och placering verifierades visuellt i den startade appen. Ingen Chaos användes.

## Version 1.2.3 — Chaos Reroller i sidhuvudet

Texten REROLLER har ersatts med `assets/chaos_reroller.png`, proportionellt skalad och inbäddad i EXE-filen. PoE 2-logotypen och snedstrecket behålls. PNG-format anges uttryckligen: Tk:s automatiska formatval läste först ett annat motiv (716×716), medan PNG-läsaren korrekt läser filens 1669×530 bildpunkter. Rätt motiv, transparens och placering verifierades visuellt i slutbygget. 87 tester och paketerat röktest passerar (`artifacts/build-1.2.3.log`, `artifacts/packaged-smoke-1.2.3.json`). Appen är startad i vanligt läge. Ingen Chaos användes.

## Version 1.2.2 — logotyp

Texten PoE 2 i appens sidhuvud har ersatts med `assets/Path_of_Exile_2_Logo.png`. Logotypen skalas proportionellt och paketeras i EXE-filen. `/ REROLLER` behålls. 87 tester och det paketerade röktestet passerar (`artifacts/build-1.2.2.log`, `artifacts/packaged-smoke-1.2.2.json`). Logotyp, transparens och layout visuellt kontrollerade i den startade EXE-filen. Ingen Chaos användes.

## Version 1.2.1 — grupperade basaffixer

- Föremålstyperna är uppdelade i nio grupper med feta, icke valbara rubriker. Sökningen behåller endast grupper som har matchande val.
- Modifierarlistan visar Base Prefixes och Base Suffixes i fet text. Endast positiva vanliga prefix/suffix för vald kategori visas, inga specialkällor. Nivåkrav kontrolleras som tidigare före crafting.
- GUI-regressionstester kontrollerar alla 81 kategoriers visade modifierar-ID:n mot respektive kategoris vanliga basaffixer. Testerna kontrollerar även fet stil, spärrat rubrikval och tangentbordsval.
- 87 automatiska tester godkända. Ingen Chaos används för denna uppdatering; craftingkedjan är oförändrad.
- Paketerad version 1.2.1 byggd och röktestad: `artifacts/packaged-smoke-1.2.1.json` visar `ok: true` och oförändrade dropdownbredder 448/448 px. Bygglogg med tester: `artifacts/build-1.2.1.log`.
- Visuellt kontrollerat i EXE: fet rubrik Vapen, sökning efter ringar under Smycken och bälten, ringarnas Base Prefixes och sökningen Resistance under Base Suffixes. Specialkällor saknas från den visade basaffixlistan. Ingen spelanslutning användes i simuleringen.

## Version 1.2.0 — katalog och två språk

- REA-import av observerade `ModsView`-datablock från indexet och alla kategorisidor: 78 `ModifiersCalc`-kategorier plus tre Waystone-nivåer, **81/81 kategorier**, inga saknade. **24 575 källposter**, **11 547 grupperade modifierarval**, inga okända numeriska format. Datum: 2026-10-19.
- Importmanifestet redovisar datum, evidens, SHA-256, gruppantal och täckning. Importskriptet normaliserar sparade datablock utan att köra webb-JavaScript.
- **85 automatiska tester** passerar, inklusive de tidigare 53 parser-/Windows-/stopp-/budget-/Shift-testerna. Nya tester täcker kategoritäckning, källhashar, specialkällor, HTML-entiteter, fasta tal, signerade decimalintervall, flerradiga affixer, tiers, fracturefamiljer, filtrering, nivåkrav och målspärrar.
- GUI-tester använder riktiga Tk-kontroller med ersatta globala hotkeys. Nätverkssocket och riktig WindowsConnection blockeras uttryckligen. Testerna verifierar lika dropdownbredd, sökning och val, språkbyte med oförändrade arbetsdata, låsta kontroller under körning, egen mall, kategoribyte, flerradig text och synlig hjälprad. Simulerat katalogmål träffar efter två appliceringar utan efterföljande applicering.
- Svenska och US English täcker samma meddelanden och formatparametrar. Alla kategorier har svenska etiketter. Backend levererar meddelandekoder och parametrar som gränssnittet översätter.
- Föremålet valideras mot valt katalogmål efter färsk stabil avläsning, före currencyval. Redan uppfyllt mål avslutas före tillgänglighetskontrollen med noll appliceringar. **Klickkedja och väntetider är oförändrade.**
- Slutlig EXE byggd med Python 3.14.7 / PyInstaller 6.22.3. `artifacts/packaged-smoke-1.2.0.json`: `ok: true`, 81 kategorier, 11 547 val, bevarat mål vid språkbyte och dropdownbredder **448/448 px**. Slutliga testresultat: `artifacts/tests-1.2.0.log` (85 godkända).
- Visuellt kontrollerat i paketerad app: svenska och US English, bevarad engelsk modifierartext och minimivärde, båda sökrutorna, alla sex hjälmvarianter, sammansatt Physical Damage/Accuracy-affix med två synliga rader och separata minima, tierdialog med källadress/nivå/intervall/vikt samt simulering som stannar efter två appliceringar vid träff. Egen mall och nedersta hjälprad ryms i standardfönstret. Popupens fokus och visning vid återöppning korrigerades och kontrollerades i slutbygget.
- Offlinekontroll: katalogen laddas från den paketerade resursen; appen har inga nätverksanrop. GUI-testerna förbjuder nätverkssocket. Datorns nätverksanslutning har inte stängts av för ett separat systemtest.
- Begränsningar: katalogen är en daterad ögonblicksbild. Egna mallar får ingen katalogbaserad kontroll av modifierarens källa. Inga nya crafting- eller hastighetsprov i spelet görs för denna version; **ingen Chaos förbrukas**.

## Tidigare genomfört

- 53 automatiska tester godkända med `python -m unittest discover -s tests -v` i version 1.1.2.
- Verkligt textunderlag från Zyon: Blight Weaver, Sinister Quarterstaff, item level 86. Avancerad fracturemarkering, rollintervall, crit och Dexterity parsas korrekt.
- Testfall omfattar rare med en förändringsbar modifierare, fractured + förändringsbar, flerradiga modifierare, implicits, numeriska gränser, redan uppfyllt mål, budget, fördröjt/identiskt/ogiltigt resultat, fokusförlust, F8, ändrad identitet/fracture, utebliven/oväntad stackminskning och stopp mellan currencyval och applicering.
- Windows x64 INPUT-strukturens storlek verifierad till 40 byte.
- Verklig Win32 clipboardlyssnare skapad och stängd utan fel.
- Byggd som portabel one-file Windowsapp med Python 3.14.7 och PyInstaller 6.22.3.
- Källkodens och den slutliga paketerade appens röktest passerar. Den paketerade appen skapar Tk-fönstret och stannar vid träff efter exakt två simulerade appliceringar i standardläge. Senaste resultat: `artifacts/packaged-smoke-1.1.2.json`.
- Paketerad app visuellt kontrollerad: layout, numeriska fält, budget, fractured-markering, Go och återaktivering av kontroller efter träff. Simuleringen visar två försök, en verifierad stackminskning och +5 melee skills vid avslut. Sista träffen ger inga ytterligare inmatningar.
- Den paketerade appen startad i vanligt läge.
- Livekalibrering F6/F7 i version 1.0.1 sparad för 3440×1440. Appens Läs föremål genomförde färsk Ctrl+Alt+C-kopiering från spelet och visade Blight Weaver, Sinister Quarterstaff, rare, ilvl 86, låst +4.99% crit och förändringsbar +20 Dexterity. Appens status och logg bekräftade noll använda orbs. Resultatet kontrollerades visuellt i den paketerade appen.

## Rättelse 1.0.1: globala kortkommandon

Det första livekalibreringsförsöket visade att F6/F7 inte sparades. Ett verkligt Windowsmeddelande postat till kortkommandolyssnaren försvann när Tk hanterade sin meddelandekö. Regressionstestet `test_hotkey_survives_tk_message_loop` reproducerade felet före ändringen och passerar efter att registrering och mottagning flyttats till en egen Windowsmeddelandetråd. F8 sätter nu även stoppflaggan direkt på lyssnartråden, oberoende av Tk-gränssnittets uppdatering. Ny livekalibrering krävs eftersom inga positioner registrerades i version 1.0.0.

Den ombyggda `.exe`-filen har även fått ett faktiskt F7-tryck medan appen hade fokus. Appen svarade med uppmaningen att aktivera PoE 2, vilket verifierar att F7 når den paketerade appens hantering. Inga craftingklick skickades. Regressionstestet verifierar dessutom att F8 sätter stoppflaggan utan någon Tk-pollning.

## Återstår i aktuell spelklient

- Längre körning för att mäta uthållig hastighet och eventuell trimning av väntetider. Standardinställningarna är konservativa startvärden, inte uppmätt maximal hastighet.
- Liveprov där själva målmodifieraren träffar; detta beteende är verifierat med automatiska tester och paketerad simulering. Den nya godkända budgeten på 20 orbs är nu helt förbrukad. Inga ytterligare craftingprov har gjorts.

## Version 1.1.0: valbart Shiftläge

- Budget större än 1 och markerat Shiftläge väljer currency en gång med vänster Shift + högerklick. Efterföljande appliceringar skickar endast enstaka vänsterklick över föremålet. Standardläget finns kvar och Shiftläget är avmarkerat vid start.
- Stabil ny föremålstext, målmatchning och oförändrad identitet/fracture krävs mellan varje applicering. Currency läses före körningen och efter budgetstopp. Vid träff eller osäkerhet hoppas stackbokföringen över och inga fler craftingklick skickas.
- Testerna verifierar ett enda currencyval, enbart efterföljande vänsterklick, två stackavläsningar för en missad serie, stopp vid första träff, identiskt resultat, budget begränsad till ursprungligt stackantal och frigjord Shift vid fokusförlust. F8 och Shift+F8 registreras separat.
- Paketerade appens **Testa Shift · 0 orbs** kördes i spelet: Blight Weaver kopierades före och efter Shift + currencyval och föremålstexterna var identiska. Appens status och logg bekräftade att inga vänsterklick eller orbs användes. Föremålet behöll `Adds 148 to 221 Fire Damage` och fractured `+4.99% to Critical Hit Chance`.
- Shift var inte nedtryckt efter provet, kontrollerat via Windows tangentstatus. Provet verifierades också visuellt i appen. Ingen ytterligare crafting har genomförts sedan det godkända enorbsprovet i version 1.0.2.
- Vid införandet av version 1.1.0 var ingen faktisk Shift-rollhastighet uppmätt. Senaste spelmätningen finns i avsnittet för version 1.1.2 nedan; röktestets och enhetstesternas hastigheter är inte spelbenchmark.

## Version 1.1.2: genomförd verifiering med totalt 20 Chaos Orbs

Zyon godkände en ny total testbudget på högst 20 Chaos Orbs, med mål minst +5 melee skill levels på samma Blight Weaver.

Det första Shiftförsöket förbrukade en orb och stoppade före nästa applicering när ingen färsk kopiering mottogs. Stacken minskade från 1152 till 1151 och föremålet fick `Leeches 7.24% of Physical Damage as Life`. Den låsta crit-modifieraren bevarades. Efterföljande diagnostikförsök utan lyckad avläsning skickade inga ytterligare appliceringar.

Felet avgränsades med ett prov utan förbrukning: första kopieringen med Shift fungerade men upprepad kopiering kunde utebli. Korta ned-/upphändelser ersattes med separata modifierar- och C-händelser med 25 ms hålltid och 25 ms för släppta tangenter. Tre upprepade Shift-avläsningar fungerade därefter. Avläsningen kan också upprepa endast kopieringskommandot inom sin tidsgräns; den upprepar aldrig craftingklick. Regressionstester täcker tappat kopieringskommando, hålltid och ovillkorlig frigöring av Ctrl/Alt/C vid stopp.

Version 1.1.2 byggdes och det paketerade röktestet passerade. Därefter sattes maxantal till **19**, så att den ursprungliga totalgränsen på 20 inte kunde överskridas:

- Den paketerade appen genomförde 19 faktiska Shift-appliceringar med verifierat nytt föremålsresultat mellan klicken.
- Stacken minskade från 1151 till 1132. Samlad förbrukning för det nya godkännandet: **20 orbs**, från 1152 till 1132.
- Appens sluträknare visade 19 försök och 19 verifierade förbrukningar för den sista körningen, med `Maxantal uppnått.` som stopporsak.
- Sista körningen tog **9,7646021 sekunder**, cirka **1,95 appliceringar/s**, inklusive för- och slutkontroller. Det är en uppmätt kortserie, inte ett bevis på maximal eller långvarig hastighet. Ingen ytterligare trimning av tider gjordes efter detta prov.
- Målstaten +5 melee träffades inte. Slutresultatet var `29% increased Physical Damage` och `+66 to Accuracy Rating` som en sammansatt modifierare, samt oförändrad fractured `+4.99% to Critical Hit Chance`.
- Shift var släppt efter körningen enligt Windows tangentstatus. Resultat, räknare och modifierare kontrollerades visuellt i appen och mot körloggen.

Underlagen finns i `artifacts/live-shift-test-1.1.2.json` och `artifacts/packaged-smoke-1.1.2.json`. Tillfällig loggning på varje kopiering togs bort före slutbygget. Appen är startad i version 1.1.2.

## Rättelse 1.0.2 och godkänt liveprov

Zyon godkände högst en vanlig Chaos Orb på Blight Weaver med mål minst +5 melee skill levels. Det första försöket stoppade före applicering: aktuell klient kopierade stackstorleken som `1\u00a0153/20` (fast mellanslag som tusentalsavskiljare). Ett regressionstest reproducerade felet. Parsern accepterar nu korrekt grupperade tal med vanligt eller fast mellanslag, smalt fast mellanslag och komma. Version 1.0.2 byggdes och röktestades före det fortsatta provet.

Det fortsatta provet i den paketerade versionen verifierade:

- Exakt ett appliceringsförsök och exakt en observerad förbrukning: stacken minskade från 1153 till 1152.
- Modifieraren `+20 to Dexterity` ersattes av `Adds 148 to 221 Fire Damage`.
- Fractured `+4.99% to Critical Hit Chance` förblev oförändrad.
- Målet träffades inte; appen stannade med `Maxantal uppnått.` utan ytterligare applicering.
- Hela körningen tog 0,9058044 sekunder, inklusive förkontroller och stackverifiering. Gränssnittets 1,10 försök/s är beräknat från detta enstaka prov och är inte ett mätvärde för maximal eller uthållig hastighet.

Resultat och uppdaterade modifierare kontrollerades visuellt i appen samt mot dess lokala körlogg. Testbudgeten är förbrukad och inga fler craftingklick skickades.

## Granskning och gränser

Koden är lokalt genomgången med särskilt fokus på klickkedjan och osäkra resultat. Qodo-granskning kunde inte köras: mappen är inget Git-repository, saknar en publicerad jämförelsebas och Qodo CLI hittades varken i PATH eller i standardmappen. Ingen extern Qodo-granskning påstås vara genomförd.

Fractured-formatet och en faktisk modifierarersättning har nu verifierats i aktuell klient. Programmet använder två stabila avläsningar och stoppar på oförändrat eller oklart resultat. Ett enda liveprov mäter inte alla möjliga serverfördröjningar. Ingen absolut nollriskgaranti för sena speluppdateringar lämnas.
