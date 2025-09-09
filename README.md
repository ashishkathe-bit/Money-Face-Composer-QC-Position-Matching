Instructions For Position Matching:

1. "Position Match Main File/main.py" file contain algorithm to simulate positions from composer.
2. Please add positions and open/close price files in "/Lean/Launcher/bin/debug/" folder.
3. Please copy content of "Position Match Main File/main.py" into /Lean/Algorithm.Python/main.py inside quant-connect environment.
4. Change composer position file path inside /Lean/Algorithm.Python/main.py as per your requirement.
5. User can find composer position files in "Composer Positions Files" folder.
6. User can get position file name from "Strategy JSON File Name to Strategy Name and Composer Link Map" Given below this instructions for given strategy.
7. Change next day close prices file path and next day open prices file path inside /Lean/Algorithm.Python/main.py as per your requirement.
8. User can find next day open and close prices files in "Next Day Close Prices And Open Prices" Folder.
9. Name format of next day open and close prices files is "next_day_open_prices_{strategy_position_file_name}.csv".
10. Inside "initialize" method, please set initial capital (self.setCash()), start date and end date for backtest.
11. User also have to load all symbols for startegy in quant connect like "self.spy_symbol = self.AddEquity("SPY", Resolution.Daily).Symbol \n self.spy_eq = self.AddEquity("SPY", Resolution.Daily) \n self.spy_eq.SetBuyingPowerModel(NullBuyingPowerModel())" inside "initialize" method.
12. Change algorithm-type-name in /Lean/Launcher/config.json to "PositionSimulation".
13. Launch task from VS code.
14. Then convert position file inside "/Lean/Launcher/bin/debug/" folder using QC_position_converter.
15. Now you have positions from quant connect, user can compare positions from both composer and quant connect in MS excel.
16. If any doubt, please contact us, we will setup simulation as per requirement.

========================================================================================================================================================================================

Strategy Position File Name to Strategy Name and Composer Link Map:

Position File Name : spec_strat_01jyjjjhe3esqbe9h2vj9j50cs_v1.csv, Strategy Name: BB-XM NASDAQ-X ||| Deez ||| 29JUN2023, Source URL: https://app.composer.trade/symphony/1hoPN3tFE0aDY3aiZtxT/details 

Position File Name : spec_strat_01jymdx1bfex1r2ctetqmrfd4g_v1.csv, Strategy Name: Bitcoin Strategy by Derecknielsen (Under Construction), Source URL: https://app.composer.trade/symphony/6nmjZHlRmBDGdwIpKycU/details

Position File Name : spec_strat_01jyme7vbpe53vbqp5wwpsbkj8_v1.csv, Strategy Name: best rebalancer | Deez | , Source URL: https://app.composer.trade/symphony/bCIMJ7nVHIQ2CCeoypYh/details

Position File Name : spec_strat_01jyme8pfwfar972846mvc2m9k_v1.csv, Strategy Name: Ease Up on the Gas V2a (add a little nitro), Source URL: https://app.composer.trade/symphony/bfDWmOdCVXh1xHw92AdJ/details      

Position File Name : spec_strat_01jymzqv0ee05bd7w38kpzw3f7_v1.csv, Strategy Name: V 3.0 | ☢️ Beta Baller + TCCC 💊 | Deez, BrianE, HinnomTX, DereckN, Garen, DJKeyhole 🧙‍♂️ | AR: 9335.3%, DD 32.3% - BT date 1D
EC19, Source URL: https://app.composer.trade/symphony/CGNGBrEjjJlOLFTyaEAa/details

Position File Name : spec_strat_01jyn8z2wne0cvpghtaabxx86x_v1.csv, Strategy Name: SPY (S&P-500) Strength Catcher  V2 Medium Risk, Medium Return, Source URL: https://app.composer.trade/symphony/GLw7YVVjLPe4d1KPX6Vc/details

Position File Name : spec_strat_01jypj4av3esavznjg34tmbp1d_v1.csv, Strategy Name: Trumper Frontrunner WM74/PAl crash catcher with VXX+ TECL KMLM Switcher+ Wash, Source URL: https://app.composer.trade/symphony/saxkDHMRwpYnADNt3hXs/details

Position File Name : spec_strat_01jyqkz180fzk8476f8hztr8c4_v1.csv, Strategy Name: Nested JRT | COST+MO / LLY+NVO / PGR+COKE, Source URL: https://app.composer.trade/symphony/PxxyRCCfleYAiQGkfXKm/details        

Position File Name : spec_strat_01jyqm7cawephspmz0dtcnqa32_v1.csv, Strategy Name: 2007 @ 2 Sharpe, Source URL: https://app.composer.trade/symphony/1MrMFYt0OWADJDHNrzS8/details

Position File Name : spec_strat_01jyqmt9e8ey9b1p5yfdn40a1c_v1.csv, Strategy Name: Anansi Portfolio | 2024-09-06, Source URL: https://app.composer.trade/symphony/ezYi3YkFHppDpwec211L/details 

Position File Name : spec_strat_01jyqmxendefb9k5abx6e8q97a_v1.csv, Strategy Name: Master Portfolio V1 (Invest Copy), Source URL: https://app.composer.trade/symphony/pWMLnAV6Nx2eCWWJKL2s/details

Position File Name : spec_strat_01jyqn28kbfss9nppjdy170jqe_v1.csv, Strategy Name: **(2015-06-11)Fund Strategy 3 117% AR ***HWRT 2.1 + Scale-in Frontrunner (UVXY)  (Invest Copy), Source URL: https://app.composer.trade/symphony/TmZj9jaaqsWwnsrFcFr5/details

Position File Name : spec_strat_01jyqn7ztpetv9et4ynyqwcsx4_v1.csv, Strategy Name: Anansi Portfolio | Public | 2025-03-01, Source URL: https://app.composer.trade/symphony/rUAat5i8upzD6sAjvUHo/details 

Position File Name : spec_strat_01jyqp1s88fnpthnaacekr6b17_v1.csv, Strategy Name: TQQQ For The Long Term Original + Frontrunner (Invest Copy), Source URL: https://app.composer.trade/symphony/nHvbB1LycC59cgQwqa2E/details

Position File Name : spec_strat_01jyqpjhs3ekqtxdd5yxn5twzk_v1.csv, Strategy Name: TQQQ Daily 60d Bond Trend, 2d Bond Trend, Drawdown, Vix (Invest Copy), Source URL: https://app.composer.trade/symphony/AAFfE3qtz2JCxAoT9Tbw/details

Position File Name : spec_strat_01jyqqnz1kfv8r5za52s8j2wk1_v1.csv, Strategy Name: BIORECKED (Invest Copy), Source URL: https://app.composer.trade/symphony/2AxWt6yYm6woMRf6ID6V/details

Position File Name : spec_strat_01jyqqqejmfc4rma2kc4941b5g_v1.csv, Strategy Name: TQQQ For The Long Term V2 (226.7% RR/46.1% Max DD) (Invest Copy), Source URL: https://app.composer.trade/symphony/DF3R1wPOvZ5kfAkQgevy/details

Position File Name : spec_strat_01jyqqrez8eca8ne9fxesqtfns_v1.csv, Strategy Name: Anti-chop QLD For The Long Term (Invest Copy), Source URL: https://app.composer.trade/symphony/Vqak65yonqLbV7S9qMpx/details    

Position File Name : spec_strat_01jyqqsf08e7mb3df897maw7cm_v1.csv, Strategy Name: 🧪 BlackSwan Portf olio | Cashen Mod (Invest Copy), Source URL: https://app.composer.trade/symphony/QKjIRxk3HKoYc5yw8XXD/details


Position File Name : spec_strat_01jyqr4pjkensseed2yx05scmc_v1.csv, Strategy Name: V7| TQQQ For The Long Term (Invest Copy), Source URL: https://app.composer.trade/symphony/kJKiNRRAvA4UZMEqTBYq/details

Position File Name : spec_strat_01jyqr5qpyf5f9k09xw4aw9xjn_v1.csv, Strategy Name: SSO, Energy, Chips, Commodities ? (Invest Copy), Source URL: https://app.composer.trade/symphony/tCu5bdNyx1cSriFS1KVJ/details  

Position File Name : spec_strat_01jyqramazewfsgjh1vr67z2je_v1.csv, Strategy Name: Sometimes TQQQ v2, Sometimes Managed Futures (Invest Copy), Source URL: https://app.composer.trade/symphony/5Py0feI7a7HzGF8lv5aV/details

Position File Name : spec_strat_01jyqrcpd8eysrmjbt0wdkf9bd_v1.csv, Strategy Name: V2.1a Holy Grail Simplified (Invest Copy), Source URL: https://app.composer.trade/symphony/D6wJxBE3ttl9rDxZiL8P/details        

Position File Name : spec_strat_01jz8ws27yfdtbn5c01h7xsdjn_v1.csv, Strategy Name: TQQQ FTLT (Sideways Market Mod) (STILL BUILDING), Source URL: https://app.composer.trade/symphony/0NBc3VHJF051reKx5Gdq/details 

Position File Name : spec_strat_01jzp39cxnehf9h5p1yw9kz2xv_v1.csv, Strategy Name: BDJ chill FR with Markov + Sector Rotator + JOSFC (Invest Copy), Source URL: https://app.composer.trade/symphony/XtLBezle0zwf9y32wP4u/details

Position File Name : spec_strat_01jzp65t29ejcvd85r9gxtqgan_v1.csv, Strategy Name: ☢️ NASDAQ-X DeETF | $Deez | BT - 14NOV2019 - AR: 346.1% DD: 38.8% - Live (Buy Copy), Source URL: https://app.composer.trade/sym
phony/A58i2tYvnHUlWVMkA4eZ/details

Position File Name : spec_strat_01jzp6cktxf6yrbb9mg4fh2dgx_v1.csv, Strategy Name: V 1.0.0 | 🦠Amoeba  | BT JAN 14 2014 | 311.8% AR, 40.5% DD (Dec 12th 2022), Source URL: https://app.composer.trade/symphony/hrw5
pt0pIszAt4QfcsCz/details

Position File Name : spec_strat_01jzp6t36kfvm8bccjpt1bmwdk_v1.csv, Strategy Name: Simple Portfolio (UVXY) + v4 Pops + BB V3.0.4.2a, Source URL: https://app.composer.trade/symphony/yqNhaX4yktJXAivjfI7e/details 

Position File Name : spec_strat_01jzpjc46nexjv3ghj5zmeev5d_v1.csv, Strategy Name: TQQQ For The Long Term V4 | No Better QQQ/SingleStocks | Pietros Maneos & Raekon mod v1 | 248.9%/46.1%DD from 28 Oct 2011 | 10 
YR Annualized Return 278.7 | 6.05 Calmar Ratio, Source URL: https://app.composer.trade/symphony/RhI15RKXGAL66g0BQrOd/details
