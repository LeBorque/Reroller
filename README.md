# PoE 2 Reroller

<img width="975" height="1085" alt="image" src="https://github.com/user-attachments/assets/e8b5c600-228c-4c1e-872b-64d0e4b5f102" />

**[DOWNLOAD HERE](https://github.com/LeBorque/Reroller/releases/download/v1.2.13/PoE2Reroller.zip)**

## English first — scroll down for Swedish / Scrolla ner för svenska

[English](#english) | [Svenska](#svenska)

## English

**Version 1.2.13:** Target minimum values sit directly below the modifier list. The maximum Chaos Orb limit has an explanation of automatic stopping, with Shift mode underneath. Dark input borders, consistent spacing, and separate counter cards make the layout easier to scan.

**Version 1.2.12:** The language selector uses `assets/se.svg` and `assets/us.svg` as the source for sharp, antialiased flags labeled **SE** and **US**. The build step renders them at their exact display size for Tkinter. The heading to the left shows **SPRÅK** or **LANGUAGE**. Select with the mouse or arrow keys and Enter; Esc closes the menu.

**Version 1.2.9:** Item types and their group headings always appear in English, even when the app language is Swedish. Other headings, buttons, and messages follow the selected language. The app icon is used for the executable, window, and taskbar. The **PoE 2 Reroller** desktop shortcut launches the packaged app.

**Keyboard shortcuts:** The calibration panel includes a compact list of key badges for calibration, emergency stop, copying, and navigation. Use F6/F7 with the game focused; F8 and Shift+F8 stop globally. Alt+Tab stops an active run when the game loses focus.

**Visual help:** Click **[SEE HOW] / [SE HUR]** beside the calibration instructions to open a large image showing the F6/F7 positions. The image displays at its original resolution, with scrollbars when needed. Close it using the red **✕ Close / ✕ Stäng** button, the window close button, or Esc.

### Version 1.2.1 — grouped lists

Item types appear under bold headings for weapons, armor, jewelry/belts, off-hand equipment, jewels, flasks/charms, relics, tablets, and waystones. The modifier list shows **only regular base affixes for the selected item type**, under bold **Base Prefixes** and **Base Suffixes** headings. Special sources no longer appear in this list. The full source catalog remains stored locally.

Search filters the choices and only displays groups with matching entries. Headings cannot be selected; use the mouse or arrow keys to select item types or affixes. Custom templates remain available. Level and threshold checks still apply; an affix may appear even if its higher tiers require a higher item level.

Previously saved special-source targets are preserved as custom templates. Select a base affix from the list to use catalog-based availability checks. The click sequence, Shift mode, and wait times are unchanged.

### New in version 1.2.0 — catalog and languages

Select **SE** (Swedish) or **US** (American English) at the top. Language changes take effect immediately while the app is idle and preserve the target, minimum values, budget, Shift setting, item reading, and calibration. Item names and modifier text remain in English in both languages. Older custom targets are migrated with Swedish as the default language.

**Item type** and **Modifier** are two equally wide, searchable dropdowns. Open a list and type in its search box. Modifiers are filtered by category, including separate armor attribute variants. The item class and base select the category automatically when the match is unambiguous; otherwise, select a category manually.

The full modifier text appears below the lists. **Modifier details** shows affix families and each tier's name, level requirement, weight, and numeric ranges. Different tiers are grouped into one choice. Fixed numbers in conditions are preserved; variable roll values become `#`. Multiline affixes stay together and receive separate minimum values.

Select **Custom template** to enter an English target manually, as described in the startup steps below. Switching categories preserves a catalog target only if the new category contains the same template, source, family, and prefix/suffix type; otherwise, the target is cleared. Custom templates are preserved.

**Go** is blocked for an incompatible item category, insufficient item level, or minimum values that regular Chaos cannot reach. If the same modifier text also exists in the regular pool, that pool's levels and value ranges are used for validation. An existing match consumes zero orbs, including fractured modifiers and modifiers from special sources. Custom templates do not receive automatic modifier availability checks; item category and normal item eligibility checks still apply.

The local catalog contains **81/81 categories**, **24,575 records**, and **11,547 grouped modifier choices**. No categories are missing from this snapshot. Later patch changes require a new import.

Nothing is downloaded at startup or during crafting. The catalog and manifest are bundled with the app. `python scripts/import_catalog.py` recreates the catalog from local import files without network access. Unknown record formats stop the import; missing categories produce an incomplete catalog that blocks crafting.

The language and stable category/modifier IDs are saved with calibration and targets. The budget must still be entered each time the app starts. Runs never resume automatically.

A portable Windows app that applies **one regular Chaos Orb at a time**, reads the result, and stops when the selected modifier appears. The interface supports Swedish and American English, with English item text. Requires windowed or borderless mode and a keyboard/mouse.

### Getting started

Open `dist/PoE2Reroller.exe`. The executable does not require a Python installation. Select **US** at the top for English.

1. Open the currency tab in English PoE 2 and place the item in its crafting slot.
2. With the game in the foreground, hover over **regular Chaos Orbs** and press **F6**. Hover over the item and press **F7**. No click is needed.
3. Click **Read item · 0 orbs** in the app. The game is activated and the item is copied using **Ctrl+Alt+C**. This consumes no currency. Return to the app with Alt+Tab to review the reading.
4. Check the name, item level, and modifiers marked **FRACTURED · LOCKED**.
5. Select a modifier or enter a template such as `+# to Level of all Melee Skills`. Enter `5` under **Minimum #1** to match +5 and higher.
6. For a modifier with multiple numbers, such as `Adds # to # Physical Damage`, enter one minimum per `#`. A text target without `#` requires an exact, case-insensitive text match.
7. Enter the required **Maximum Chaos Orbs** and click **Go**. This starts crafting with that budget. If the target is already present, no orb is used.
8. Leave the mouse and keyboard alone until the run stops. **F8** is the global emergency stop. The Stop button also works, but Alt+Tab already stops the run when the game loses focus.

If another program uses F8, it must release the shortcut before the app can start a run. F6/F7 only work while PoE 2 has focus. Moving the game window or changing its resolution requires recalibration. Do not hold Shift, Ctrl, Alt, or mouse buttons during a run.

### Fractured items and items with few modifiers

Supported items include rares with one changeable modifier, rares with one fractured and one changeable modifier, and rares with more modifiers. There is no minimum total modifier count. Regular Chaos Orbs cannot be used on magic items.

Advanced copying identifies fractured modifiers using markers such as `{ Fractured Suffix Modifier ... }`. The parser was verified against Zyon's copied Blight Weaver, Sinister Quarterstaff, item level 86: locked `+4.99% to Critical Hit Chance` and changeable `+20 to Dexterity`. Numeric roll ranges in parentheses are removed before target matching.

Targets are checked against explicit modifiers, including fractured modifiers. Implicits, runes, and enchants do not count as rerollable targets. Every identified fractured modifier must remain unchanged during the run. The item must be identified and must not be corrupted, mirrored, or sanctified.

### Speed and stopping

#### Optional Shift mode (version 1.1.0)

**Test Shift · 0 orbs** selects currency using Shift + right-click, hovers over the item, and tests three repeated Ctrl+Alt+C copies while keeping Shift held. It sends no left-clicks and consumes no orbs. On completion, Shift is released and any remaining currency selection is canceled with Esc while the game still has focus.

Enable **Shift mode** for budgets greater than 1. The stack is selected once and the mouse stays over the item between rolls. Each application is still followed by a stable reading, an identity check, and a target check. No click sequence is queued. A budget of 1 uses standard mode.

In Shift mode, the stack is read before the run and after stopping without a match, avoiding a trip to the stack after every roll. During the run, the app therefore displays application attempts; verified consumption is updated after the final check. A match or error stops further crafting clicks and skips stack accounting. The run is limited to the smaller of the budget and the initially read stack size, preventing continued clicks after the stack is exhausted. An empty or unreadable final stack causes a conservative stop without a verified total.

The app holds only left Shift and releases its own Shift input even if focus is lost. Both F8 and Shift+F8 stop the run; both must be available for Shift mode. Esc may close the stash if currency selection has already ended. Never resume manually with an uncertain currency selection: cancel with Esc and start a new run.

Version 1.1.2 was tested in the game with 19 Shift applications in 9.76 seconds, approximately 1.95 applications/second including checks, following one initial diagnostic roll within the same approved total budget of 20. The target modifier did not appear in that test. The budget stop, stack consumption, unchanged fracture, and released Shift were verified. This speed applies to that short test and is not a guaranteed maximum.

#### Standard mode

The run is sequential: apply → read the new result → check the target → verify a stack decrease → next application. A new result requires two matching fresh readings over at least 80 ms. There is no click queue or batch rolling.

A clipboard update alone is insufficient: the copied modifier set must differ from the previous result and stabilize. Repeatedly reading the same result produces no additional crafting clicks. An uncertain result stops the run after 3 seconds. A legitimate reroll with identical values also stops the run; this is intentional.

Loss of focus, a changed game window, changed item identity/fractured modifiers, a disturbed mouse position, incorrect currency, or an empty/unreadable stack stops the run. The app never automatically retries a crafting click after an uncertain application command.

No finite number of screen/clipboard readings can prove that the game server will never send a later update. No zero-risk guarantee or verified live speed is provided before crafting tests in the current client. Default timings are conservative starting values, not a measured maximum speed. They should only be changed in the source after approved live tests.

- **Attempts:** sent or uncertain application commands, always limited by the budget.
- **Verified consumption:** an observed stack decrease of exactly one after a verified result without a match.
- On a **match**, input stops immediately, even before another stack reading. The last orb's consumption may therefore remain unverified in the counter.
- After the last Chaos Orb is used, an empty slot cannot be copied. The app then stops conservatively; any match is checked before the stack reading.

If the run stops after currency selection but before application, currency may remain on the cursor. Activate the game and press Esc to cancel it. The app does not send Esc after losing focus, avoiding interference with another app.

### Local storage

Calibration and targets are saved in `%LOCALAPPDATA%/PoE2Reroller/settings.json`. The budget is not saved and must be entered each time the app starts. Runs never resume automatically. The local log rotates and contains run status and counters, with no account details. The app makes no network requests.

Reading an item replaces the contents of the Windows clipboard. Save any clipboard content you want to keep before using the app.

### Source code, tests, and building

Python 3.14 on Windows, using the standard library at runtime. Build dependencies are listed in `requirements-build.txt`.

```powershell
python main.py
python main.py --demo
python -m unittest discover -s tests -v
python -m pip install -r requirements-build.txt
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

`--demo` is clearly marked SIMULATION and uses no game functions, real orbs, or saved calibration. Simulated speed is not in-game speed.

For a packaged smoke test, which opens and closes a simulated app window:

```powershell
.\dist\PoE2Reroller.exe --smoke-test .\artifacts\smoke.json
```

Create `artifacts` first. The test result should contain `ok: true`, `gui_created: true`, and exactly two simulated applications before a match.

Actual in-game consumption and speed tests require a confirmed test item and orb limit first. See `VERIFICATION.md` for completed checks and remaining live tests.

---

## Svenska

**Version 1.2.13:** Målets minimivärden ligger direkt under modifierarlistan. Maxantal Chaos Orbs förklaras som en förbrukningsgräns med automatiskt stopp, med Shiftläge under. Mörka fältkanter, jämnare avstånd och separata räknarkort gör gränssnittet lättare att överblicka.

**Version 1.2.12:** Språkväljaren använder `assets/se.svg` och `assets/us.svg` som källa för skarpa, kantutjämnade flaggor med **SE** och **US**. Byggsteget renderar dem till exakt visningsstorlek för Tkinter. Rubriken till vänster visar **SPRÅK** eller **LANGUAGE**. Välj med musen eller piltangenterna och Enter; Esc stänger menyn.

**Version 1.2.9:** Föremålstyper och deras grupprubriker är alltid engelska, även när appens språk är svenska. Övriga rubriker, knappar och meddelanden följer språkvalet. Appens ikon används för programfilen, fönstret och aktivitetsfältet. Genvägen **PoE 2 Reroller** på skrivbordet startar den paketerade appen.

**Kortkommandon:** Kalibreringspanelen visar en kompakt lista med tangentbrickor för kalibrering, nödstopp, kopiering och navigering. F6/F7 används med spelet i fokus; F8 och Shift+F8 stoppar globalt. Alt+Tab stoppar en aktiv körning när spelet tappar fokus.

**Bildhjälp:** Klicka **[SE HUR] / [SEE HOW]** bredvid kalibreringsinstruktionen för att öppna en stor bild av F6-/F7-positionerna. Bilden visas i originalupplösning med rullningslister vid behov. Stäng med den röda **✕ Stäng / ✕ Close**-knappen, fönsterkrysset eller Esc.

### Version 1.2.1 — grupperade listor

Föremålstyperna visas under feta rubriker för vapen, rustningar, smycken/bälten, sidohandsutrustning, juveler, flaskor/charms, reliker, tavlor och vägstenar. Modifierarlistan visar nu **endast vanliga basaffixer för vald föremålstyp**, under de feta rubrikerna **Base Prefixes** och **Base Suffixes**. Specialkällor visas inte längre i denna lista. Källkatalogen behålls oförändrad lokalt.

Sökning filtrerar valen och visar bara grupper med träffar. Rubrikerna är inte valbara; mus och piltangenter väljer själva föremålstyperna eller affixerna. Egen mall finns kvar. Nivå- och gränsvärdeskontroller sker som tidigare; en affix kan visas även om högre tiers kräver högre item level.

Tidigare sparade mål från specialkällor bevaras som egna mallar. För katalogbaserad tillgänglighetskontroll väljer du en basaffix i listan. Klickkedja, Shiftläge och väntetider är oförändrade.

### Nytt i version 1.2.0 — katalog och språk

Välj **SE** (svenska) eller **US** (amerikansk engelska) överst. Språkbyte sker direkt när appen är inaktiv och bevarar mål, minimivärden, budget, Shiftval, avläst föremål och kalibrering. Engelska föremålsnamn och modifierartexter behålls i båda språken. Äldre egna mål migreras med svenska som standardspråk.

**Föremålstyp** och **Modifierare** är två lika breda sökbara dropdowns. Klicka i en lista och skriv i sökrutan. Modifierarna filtreras efter kategori, inklusive rustningarnas attributvarianter. Klassen och basen väljer kategori automatiskt när träffen är entydig; annars krävs ett kategorival.

Hela modifierartexten visas under listorna. **Modifierardetaljer** visar affixfamiljer och varje tiers namn, nivåkrav, vikt och numeriska intervall. Olika tiers samlas i ett val. Fasta tal i villkor bevaras; markerade rollvärden blir `#`. Flerradiga affixer hålls ihop och får separata minimivärden.

Välj **Egen mall** för att skriva ett eget engelskt mål enligt startstegen nedan. Ett kategoribyte bevarar ett katalogmål bara om samma mall, källa, familj och prefix/suffix finns i den nya kategorin; annars rensas det. Egna mallar bevaras.

**Go** spärras vid fel föremålskategori, för låg item level eller minimivärden som inte kan nås med vanlig Chaos. Finns samma modifierartext även i den vanliga poolen används dess nivåer och värdeintervall för kontrollen. Ett mål som redan finns ger noll förbrukning, även om det är fractured eller kommer från en specialkälla. Egna mallar får ingen automatisk kontroll av modifierarens tillgänglighet; föremålskategori och vanliga föremålskrav kontrolleras fortfarande.

Den lokala katalogen omfattar **81/81 kategorier**, **24 575 poster** och **11 547 grupperade modifierarval**. Inga kategorier saknas. Det är en daterad ögonblicksbild; senare patchändringar kräver en ny import.

Ingen hämtning sker vid start eller crafting. Katalog och manifest är inbäddade i appen. `python scripts/import_catalog.py` återskapar katalogen från de lokala importunderlagen utan nätverk. Okänt postformat stoppar importen; saknade kategorier ger ofullständig katalog som spärrar crafting.

Språk och stabila kategori-/modifierar-ID:n sparas med kalibrering och mål. Budget måste fortfarande anges vid varje programstart. Ingen körning återupptas automatiskt.

Portabel Windowsapp för att använda **en vanlig Chaos Orb åt gången**, läsa resultatet och stanna vid vald modifierare. Svensk eller amerikansk engelsk programtext, engelska föremålstexter. Kräver fönsterläge eller kantlöst läge och tangentbord/mus.

### Starta

Öppna `dist/PoE2Reroller.exe`. Ingen Pythoninstallation krävs för `.exe`-filen.

1. Öppna currencyfliken i PoE 2 och placera föremålet i craftingrutan.
2. Med spelet i förgrunden: hovra **vanliga Chaos Orbs**, tryck **F6**. Hovra föremålet, tryck **F7**. Inget klick behövs.
3. Klicka **Läs föremål · 0 orbs** i appen. Spelet aktiveras och föremålet kopieras med **Ctrl+Alt+C**. Detta använder ingen currency. Återvänd till appen med Alt+Tab för att kontrollera avläsningen.
4. Kontrollera namn, item level och modifierarna märkta **FRACTURED · LÅST**.
5. Välj en modifierare eller skriv exempelvis `+# to Level of all Melee Skills`. Ange `5` under **Minst #1**. Då matchar +5 och högre.
6. För en modifierare med flera tal, exempelvis `Adds # to # Physical Damage`, ange ett minimivärde per `#`. Ett textmål utan `#` kräver exakt text (skiftlägesokänsligt).
7. Ange obligatoriskt **maxantal Chaos Orbs** och tryck **Go**. Go startar crafting med den budgeten. Om målet redan finns används ingen orb.
8. Låt mus och tangentbord vara tills körningen stoppar. **F8** är globalt nödstopp. Stoppknappen fungerar också, men Alt+Tab stoppar redan körningen vid fokusförlust.

Om ett annat program använder F8 måste det släppa kortkommandot innan appen kan starta en körning. F6/F7 fungerar endast när PoE 2 har fokus. Flyttat fönster eller ändrad upplösning kräver ny kalibrering. Håll inte Shift, Ctrl, Alt eller musknappar nere under körning.

### Fractured och föremål med få modifierare

Rare med en förändringsbar modifierare stöds, liksom rare med en fractured och en förändringsbar modifierare och rare med fler modifierare. Det finns inget minimikrav på totalt antal modifierare. Magic accepteras inte av vanlig Chaos Orb.

Avancerad kopiering identifierar fractured med exempelvis `{ Fractured Suffix Modifier ... }`. Parsern är verifierad mot Zyons kopierade Blight Weaver, Sinister Quarterstaff, ilvl 86: låst `+4.99% to Critical Hit Chance` och förändringsbar `+20 to Dexterity`. Numeriska rollintervall i parentes tas bort före målmatchning.

Målet söks bland explicita modifierare inklusive fractured; implicit, runor och enchants räknas inte som rullbara mål. Varje identifierad fractured modifierare måste vara oförändrad under körningen. Föremålet måste vara identifierat och får inte vara corrupted, mirrored eller sanctified.

### Hastighet och stopp

#### Valbart Shiftläge (version 1.1.0)

**Testa Shift · 0 orbs** väljer currency med Shift + högerklick, hovrar föremålet och provar tre upprepade Ctrl+Alt+C-kopieringar med Shift kvar nere. Det skickar inga vänsterklick och använder inga orbs. Vid avslut släpps Shift och kvarvarande currencyläge avbryts med Esc när spelet fortfarande har fokus.

Markera **Shiftläge** för körningar med maxantal större än 1. Stacken väljs en gång och musen stannar över föremålet mellan rolls. Varje applicering följs fortfarande av stabil avläsning, identitetskontroll och måltest. Ingen klickserie köas. För en budget på 1 används standardläget.

I Shiftläge läses stacken före körningen och efter avslut vid missad målstat, vilket tar bort stackresorna efter varje roll. Under körningen visas därför appliceringsförsök; verifierad förbrukning uppdateras efter slutkontrollen. Vid träff eller fel skickas inga fler craftingklick och stackbokföringen hoppas över. Körningen begränsas till det lägsta av budgeten och den ursprungligen lästa stackstorleken, så den inte fortsätter klicka när stacken har förbrukats. Tom eller oläsbar slutstack ger ett konservativt stopp utan verifierad totalsiffra.

Appen håller endast vänster Shift och släpper sin egen Shift även vid fokusförlust. Både F8 och Shift+F8 stoppar; båda måste vara lediga för Shiftläge. Esc kan stänga stashen om currencyläget redan har upphört. Återuppta aldrig manuellt med ett oklart currencyläge: avbryt med Esc och starta en ny körning.

Version 1.1.2 verifierades i spelet med en serie på 19 Shift-appliceringar på 9,76 sekunder, cirka 1,95 appliceringar/s inklusive kontroller, efter en inledande diagnostikroll inom samma godkända totalbudget på 20. Målstaten träffades inte i provet; budgetstopp, stackförbrukning, oförändrad fracture och släppt Shift verifierades. Hastigheten gäller den korta provserien och är inte en garanterad maximal hastighet.

#### Standardläge

Körningen är sekventiell: applicera → läs nytt resultat → kontrollera målet → verifiera stackminskning → nästa applicering. Två överensstämmande färska avläsningar över minst 80 ms krävs för ett nytt resultat. Det finns ingen klickkö och inga batchrolls.

En clipboarduppdatering räcker inte: den kopierade modifieraruppsättningen måste skilja sig från föregående resultat och stabiliseras. Upprepad läsning av samma resultat ger inga fler craftingklick. Efter 3 sekunders oklart resultat stoppas körningen. En legitim identisk återrullning stoppar också; detta är avsiktligt.

Fokusförlust, ändrat spelfönster, ändrad identitet/fractured, störd musposition, fel currency eller tom/oläsbar stack stoppar körningen. Programmet klickar aldrig om automatiskt efter ett osäkert appliceringskommando.

Ingen ändlig mängd skärm-/clipboardavläsningar kan bevisa att spelservern aldrig skickar en senare uppdatering. Ingen nollriskgaranti eller verifierad livehastighet lämnas före craftingtest i aktuell klient. Standardtiderna är konservativa startvärden, inte uppmätt maximal hastighet. De ska bara ändras i källkoden efter godkända liveprov.

- **Försök**: skickade eller osäkra appliceringskommandon, alltid begränsade av budgeten.
- **Verifierad förbrukning**: observerad stackminskning med exakt en efter ett verifierat missat resultat.
- Vid **träff** stoppas inmatning direkt, även före ytterligare stackavläsning. Sista orbens förbrukning kan därför vara overifierad i räknaren.
- När sista Chaos Orb används kan en tom ruta inte kopieras. Appen stoppar då konservativt; en eventuell träff kontrolleras före stackavläsningen.

Om stopp sker efter att currency valts men före applicering kan currency finnas kvar på pekaren. Aktivera spelet och tryck Esc för att avbryta det. Appen skickar inte Esc efter fokusförlust och riskerar därför inte att stänga en annan app.

### Lokal lagring

Kalibrering och mål sparas i `%LOCALAPPDATA%/PoE2Reroller/settings.json`. Budget sparas inte och måste anges vid varje programstart. Ingen körning återupptas automatiskt. Lokal logg roteras och innehåller körstatus och räknare, inga kontouppgifter. Inga nätverksanrop görs av appen.

Avläsningen ersätter innehållet i Windows clipboard. Kopiera det du vill behålla före användning.

### Källkod, tester och bygge

Python 3.14 på Windows, standardbibliotek för runtime. Byggberoendet finns i `requirements-build.txt`.

```powershell
python main.py
python main.py --demo
python -m unittest discover -s tests -v
python -m pip install -r requirements-build.txt
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

`--demo` är tydligt märkt SIMULERING och använder inga spelfunktioner, riktiga orbs eller sparad kalibrering. Simulerad hastighet är inte spelhastighet.

För paketerat röktest (öppnar och stänger ett simulerat appfönster):

```powershell
.\dist\PoE2Reroller.exe --smoke-test .\artifacts\smoke.json
```

Skapa `artifacts` först. Testresultatet ska ha `ok: true`, `gui_created: true` och exakt två simulerade appliceringar till träff.

Faktisk förbrukning och hastighetsmätning i spelet utförs först med bekräftat testföremål och bekräftad orbgräns. Se `VERIFICATION.md` för genomförda kontroller och kvarvarande liveprov.
