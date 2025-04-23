# // This Pine Script™ code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
# // © fluxchart

# //@version=6
# //S&R V2.12
# const bool DEBUG = false
# const bool fixSRs = true
# const bool fixRetests = false

# indicator("Support & Resistance (MTF) | Flux Charts", overlay = true, max_labels_count = 500, max_lines_count = 500, max_boxes_count = 500, dynamic_requests = true)

# const int maxSRInfoListSize = 10
# const int maxBarInfoListSize = 3000
# const int maxDistanceToLastBar = 500
# const int minSRSize = 5
# const int retestLabelCooldown = 3
# const float tooCloseATR = 1.0 / 8.0
# const int labelOffsetBars = 20

# const int atrLen = 20
# atr = ta.atr(atrLen)
# avgVolume = ta.sma(volume, atrLen)

# var int curTFMS = timeframe.in_seconds(timeframe.period) * 1000
# var map<string, bool> alerts = map.new<string, bool>()
# alerts.put("Retest", false)
# alerts.put("Break", false)

# srPivotLength = input.int(15, "Pivot Length", minval = 3, maxval = 50, group = "General Configuration", display = display.none)
# srStrength = input.int(1, "Strength", [1, 2, 3], group = "General Configuration", display = display.none)
# srInvalidation = input.string("Close", "Invalidation", ["Wick", "Close"], group = "General Configuration", display = display.none)
# expandZones = input.string("Only Valid", "Expand Lines & Zones", options = ["All", "Only Valid", "None"], group = "General Configuration", display = display.none)
# showInvalidated = input.bool(true, "Show Invalidated", group = "General Configuration", display = display.none)

# timeframe1Enabled = input.bool(true, title = "", group = "Timeframes", inline = "timeframe1", display = display.none)
# timeframe1 = input.timeframe("", title = "", group = "Timeframes", inline = "timeframe1", display = display.none)
# timeframe2Enabled = input.bool(false, title = "", group = "Timeframes", inline = "timeframe2", display = display.none)
# timeframe2 = input.timeframe("D", title = "", group = "Timeframes", inline = "timeframe2", display = display.none)
# timeframe3Enabled = input.bool(false, title = "", group = "Timeframes", inline = "timeframe3", display = display.none)
# timeframe3 = input.timeframe("W", title = "", group = "Timeframes", inline = "timeframe3", display = display.none)

# showBreaks = input.bool(true, "Show Breaks", group = "Breaks & Retests", inline = "ShowBR", display = display.none)
# showRetests = input.bool(true, "Show Retests", group = "Breaks & Retests", inline = "ShowBR", display = display.none)
# avoidFalseBreaks = input.bool(false, "Avoid False Breaks", group = "Breaks & Retests", display = display.none)
# breakVolumeThreshold = input.float(0.3, "Break Volume Threshold", minval = 0.1, maxval = 2.0, step = 0.1, group = "Breaks & Retests", tooltip = "Only taken into account if Avoid False Breakouts is enabled.\nHigher values mean it's less likely to be a break.", display = display.none)
# inverseBrokenLineColor = input.bool(false, "Inverse Color After Broken", group = "Breaks & Retests", display = display.none)

# styleMode = input.string("Lines", "Style", ["Lines", "Zones"], group = "Style", display = display.none)
# lineStyle = input.string("____", "Line Style", ["____", "----", "...."], group = "Style", display = display.none)
# lineWidth = input.int(2, "Line Width", minval = 1, group = "Style", display = display.none)
# zoneSize = input.float(1.0, "Zone Width", minval = 0.1, maxval = 10, step = 0.1, group = "Style", display = display.none)
# zoneSizeATR = zoneSize * 0.075
# supportColor = input.color(#08998180, "Support Color", group = "Style", inline = "RScolors", display = display.none)
# resistanceColor = input.color(#f2364580, "Resistance Color", group = "Style", inline = "RScolors", display = display.none)
# breakColor = input.color(color.blue, "Break Color", group = "Style", inline = "RScolors2", display = display.none)
# textColor = input.color(#ffffff80, "Text Color", group = "Style", inline = "RScolors2", display = display.none)

# enableRetestAlerts = input.bool(true, "Enable Retest Alerts", tooltip = "Needs Show Retests option enabled.", group = "Alerts", display = display.none)
# enableBreakAlerts = input.bool(true, "Enable Break Alerts", tooltip = "Needs Show Breaks option enabled.", group = "Alerts", display = display.none)

# insideBounds = (bar_index > last_bar_index - maxDistanceToLastBar)

# type srInfo
#     int startTime
#     float price
#     string srType
#     int strength
#     string timeframeStr
#     bool ephemeral = false

#     int breakTime
#     array<int> retestTimes

# type srObj
#     srInfo info
    
#     bool startFixed
#     bool breakFixed

#     bool rendered
#     string combinedTimeframeStr

#     line srLine
#     box srBox
#     label srLabel
#     label breakLabel
#     array<label> retestLabels

# type barInfo
#     int t
#     int tc
#     float c
#     float h
#     float l

# var allSRList = array.new<srObj>()

# //#region Find Val RTN Time
# findValRtnTime (barInfo[] biList, valToFind, toSearch, searchMode, minTime, maxTime, int defVal = na) =>
#     int rtnTime = defVal
#     float minDiff = na
#     if biList.size() > 0
#         for i = biList.size() - 1 to 0
#             curBI = biList.get(i)
#             if curBI.t >= minTime and curBI.t < maxTime
#                 toLook = (toSearch == "Low" ? curBI.l : toSearch == "High" ? curBI.h : curBI.c)
#                 if searchMode == "Nearest"
#                     curDiff = math.abs(valToFind - toLook)
#                     if na(minDiff)
#                         rtnTime := curBI.t
#                         minDiff := curDiff
#                     else
#                         if curDiff <= minDiff
#                             minDiff := curDiff
#                             rtnTime := curBI.t
#                 if searchMode == "Higher"
#                     if toLook >= valToFind
#                         rtnTime := curBI.t
#                         break
#                 if searchMode == "Lower"
#                     if toLook <= valToFind
#                         rtnTime := curBI.t
#                         break
#     rtnTime
# //#endregion

# formatTimeframeString (string formatTimeframe, bool short = false) =>
#     timeframeF = (formatTimeframe == "" ? timeframe.period : formatTimeframe)
#     if str.contains(timeframeF, "D") or str.contains(timeframeF, "W") or str.contains(timeframeF, "S") or str.contains(timeframeF, "M")
#         timeframe.from_seconds(timeframe.in_seconds(timeframeF))
#     else
#         seconds = timeframe.in_seconds(timeframeF)
#         if seconds >= 3600
#             hourCount = int(seconds / 3600)
#             if short
#                 str.tostring(hourCount) + "h"
#             else
#                 str.tostring(hourCount) + " Hour" + (hourCount > 1 ? "s" : "")
#         else
#             if short
#                 timeframeF + "m"
#             else
#                 timeframeF + " Min"

# renderSRObj (srObj sr) =>
#     if na(sr.info.breakTime) or showInvalidated
#         sr.rendered := true
#         endTime = nz(sr.info.breakTime, time + curTFMS * labelOffsetBars)
#         extendType = extend.none
#         if na(sr.info.breakTime)
#             extendType := extend.right
#         if expandZones == "Only Valid" and na(sr.info.breakTime)
#             extendType := extend.both
#         else if expandZones == "All"
#             extendType := extend.both
#             endTime := time + curTFMS * labelOffsetBars
        
#         labelTitle = formatTimeframeString(sr.info.timeframeStr)
#         if not na(sr.combinedTimeframeStr)
#             labelTitle := sr.combinedTimeframeStr

#         labelTitle += " | " + str.tostring(sr.info.price, format.mintick) + ((sr.info.ephemeral and DEBUG) ? " [E]" : "")
#         if styleMode == "Lines"
#             // Line
#             sr.srLine := line.new(sr.info.startTime, sr.info.price, endTime, sr.info.price, xloc = xloc.bar_time, color = sr.info.srType == "Resistance" ? resistanceColor : supportColor, width = lineWidth, style = lineStyle == "----" ? line.style_dashed : lineStyle == "...." ? line.style_dotted : line.style_solid, extend = extendType)
#             // Label
#             sr.srLabel := label.new(extendType == extend.none ? ((sr.info.startTime + endTime) / 2) : endTime, sr.info.price, xloc = xloc.bar_time, text = labelTitle, textcolor = textColor, style = label.style_none)
#         else
#             // Zone
#             sr.srBox := box.new(sr.info.startTime, sr.info.price + atr * zoneSizeATR, endTime, sr.info.price - atr * zoneSizeATR, xloc = xloc.bar_time, bgcolor = sr.info.srType == "Resistance" ? resistanceColor : supportColor, border_color = na, text = labelTitle, text_color = textColor, extend = extendType, text_size = size.normal, text_halign = (extendType != extend.none) ? text.align_right : text.align_center)

#         // Break Label
#         if showBreaks
#             if not na(sr.info.breakTime)
#                 sr.breakLabel := label.new(sr.info.breakTime, sr.info.price, "B", yloc = sr.info.srType ==  "Resistance" ? yloc.belowbar : yloc.abovebar, style = sr.info.srType == "Resistance" ? label.style_label_up : label.style_label_down, color = breakColor, textcolor = color.new(textColor, 0), xloc = xloc.bar_time, size = size.small)
#                 if (time - curTFMS <= sr.info.breakTime) and (time + curTFMS >= sr.info.breakTime)
#                     alerts.put("Break", true)

#         // Retest Labels
#         if showRetests
#             if sr.info.retestTimes.size() > 0
#                 for i = sr.info.retestTimes.size() - 1 to 0
#                     curRetestTime = sr.info.retestTimes.get(i)
#                     cooldownOK = true
#                     if sr.retestLabels.size() > 0
#                         lastLabel = sr.retestLabels.get(0)
#                         if math.abs(lastLabel.get_x() - curRetestTime) < curTFMS * retestLabelCooldown
#                             cooldownOK := false

#                     if cooldownOK and (curRetestTime >= sr.info.startTime) and (na(sr.info.breakTime) or curRetestTime < sr.info.breakTime)
#                         if time - curTFMS <= curRetestTime and time >= curRetestTime
#                             alerts.put("Retest", true)
#                         sr.retestLabels.unshift(label.new(curRetestTime, sr.info.price, "R" + (DEBUG ?  (" " + str.tostring(sr.info.price)) : ""), yloc = sr.info.srType ==  "Resistance" ? yloc.abovebar : yloc.belowbar, style = sr.info.srType == "Resistance" ? label.style_label_down : label.style_label_up, color = sr.info.srType == "Resistance" ? resistanceColor : supportColor, textcolor = color.new(textColor, 0), xloc = xloc.bar_time, size = size.small))

# safeDeleteSRObj (srObj sr) =>
#     if sr.rendered
#         line.delete(sr.srLine)
#         box.delete(sr.srBox)
#         label.delete(sr.srLabel)
#         label.delete(sr.breakLabel)
#         if sr.retestLabels.size() > 0
#             for i = 0 to sr.retestLabels.size() - 1
#                 curRetestLabel = sr.retestLabels.get(i)
#                 label.delete(curRetestLabel)
#         sr.rendered := false

# var allSRInfoList = array.new<srInfo>()
# var barInfoList = array.new<barInfo>()

# pivotHigh = ta.pivothigh(srPivotLength, srPivotLength)
# pivotLow = ta.pivotlow(srPivotLength, srPivotLength)

# barInfoList.unshift(barInfo.new(time, time_close, close, high, low))
# if barInfoList.size() > maxBarInfoListSize
#     barInfoList.pop()

# if insideBounds and barstate.isconfirmed
#     // Find Supports
#     if not na(pivotLow)
#         validSR = true
#         if allSRInfoList.size() > 0
#             for i = 0 to allSRInfoList.size() - 1
#                 curRSInfo = allSRInfoList.get(i)
#                 if (math.abs(curRSInfo.price - pivotLow) < atr * tooCloseATR) and na(curRSInfo.breakTime)
#                     validSR := false
#                     break
        
#         if validSR
#             newSRInfo = srInfo.new(barInfoList.get(srPivotLength).t, pivotLow, "Support", 1, timeframe.period)
#             newSRInfo.retestTimes := array.new<int>()

#             //for i = 1 to srPivotLength
#                 //curBI = barInfoList.get(i)
#                 //if (curBI.l <= newSRInfo.price and curBI.c >= newSRInfo.price)
#                     //newSRInfo.strength += 1
#                     //if curBI.t != newSRInfo.startTime
#                         //newSRInfo.retestTimes.unshift(curBI.t)
            
#             allSRInfoList.unshift(newSRInfo)
#             while allSRInfoList.size() > maxSRInfoListSize
#                 allSRInfoList.pop()
    
#     // Find Resistances
#     if not na(pivotHigh)
#         validSR = true
#         if allSRInfoList.size() > 0
#             for i = 0 to allSRInfoList.size() - 1
#                 curRSInfo = allSRInfoList.get(i)
#                 if (math.abs(curRSInfo.price - pivotLow) < atr * tooCloseATR) and na(curRSInfo.breakTime)
#                     validSR := false
#                     break
#         if validSR
#             newSRInfo = srInfo.new(barInfoList.get(srPivotLength).t, pivotHigh, "Resistance", 1, timeframe.period)
#             newSRInfo.retestTimes := array.new<int>()

#             //for i = 1 to srPivotLength
#                 //curBI = barInfoList.get(i)
#                 //if (curBI.h >= newSRInfo.price and curBI.c <= newSRInfo.price)
#                     //newSRInfo.strength += 1
#                     //if curBI.t != newSRInfo.startTime
#                         //newSRInfo.retestTimes.unshift(curBI.t)

#             allSRInfoList.unshift(newSRInfo)
#             if allSRInfoList.size() > maxSRInfoListSize
#                 allSRInfoList.pop()

# // Handle SR Infos
# if insideBounds and (srInvalidation == "Wick" or barstate.isconfirmed)
#     if allSRInfoList.size() > 0
#         for i = 0 to allSRInfoList.size() - 1
#             srInfo curSRInfo = allSRInfoList.get(i)
            
#             // Breaks
#             invHigh = (srInvalidation == "Close" ? close : high)
#             invLow = (srInvalidation == "Close" ? close : low)
#             closeTime = time
#             if na(curSRInfo.breakTime)
#                 if curSRInfo.srType == "Resistance" and invHigh > curSRInfo.price
#                     if (not avoidFalseBreaks) or (volume > avgVolume * breakVolumeThreshold)
#                         curSRInfo.breakTime := closeTime
#                         if inverseBrokenLineColor and (not curSRInfo.ephemeral) and curSRInfo.strength >= srStrength
#                             ephSR = srInfo.new(closeTime, curSRInfo.price, "Support", curSRInfo.strength, curSRInfo.timeframeStr, true)
#                             ephSR.retestTimes := array.new<int>()
#                             allSRInfoList.unshift(ephSR)
#                 else if curSRInfo.srType == "Support" and invLow < curSRInfo.price
#                     if (not avoidFalseBreaks) or (volume > avgVolume * breakVolumeThreshold)
#                         curSRInfo.breakTime := closeTime
#                         if inverseBrokenLineColor and (not curSRInfo.ephemeral) and curSRInfo.strength >= srStrength
#                             ephSR = srInfo.new(closeTime, curSRInfo.price, "Resistance", curSRInfo.strength, curSRInfo.timeframeStr, true)
#                             ephSR.retestTimes := array.new<int>()
#                             allSRInfoList.unshift(ephSR)
                
#             // Strength & Retests
#             if na(curSRInfo.breakTime) and time > curSRInfo.startTime and barstate.isconfirmed
#                 if curSRInfo.srType == "Resistance" and high >= curSRInfo.price and close <= curSRInfo.price
#                     int lastRetestTime = 0
#                     if curSRInfo.retestTimes.size() > 0
#                         lastRetestTime := curSRInfo.retestTimes.get(0)
                    
#                     if lastRetestTime != time
#                         if not curSRInfo.ephemeral
#                             curSRInfo.strength += 1
#                         curSRInfo.retestTimes.unshift(time)
                
#                 else if curSRInfo.srType == "Support" and low <= curSRInfo.price and close >= curSRInfo.price
#                     int lastRetestTime = 0
#                     if curSRInfo.retestTimes.size() > 0
#                         lastRetestTime := curSRInfo.retestTimes.get(0)
                    
#                     if lastRetestTime != time
#                         if not curSRInfo.ephemeral
#                             curSRInfo.strength += 1
#                         curSRInfo.retestTimes.unshift(time)

# fixSRToTimeframe (srObj sr) =>
#     srMS = math.max(timeframe.in_seconds(sr.info.timeframeStr), timeframe.in_seconds()) * 1000
#     if (not sr.startFixed)
#         if not sr.info.ephemeral
#             if sr.info.srType == "Resistance"
#                 sr.info.startTime := findValRtnTime(barInfoList, sr.info.price, "High", "Nearest", sr.info.startTime - srMS, sr.info.startTime + srMS, sr.info.startTime)
#             else
#                 sr.info.startTime := findValRtnTime(barInfoList, sr.info.price, "Low", "Nearest", sr.info.startTime - srMS, sr.info.startTime + srMS, sr.info.startTime)
#             sr.startFixed := true
#         else
#             if allSRList.size() > 0
#                 for i = 0 to allSRList.size() - 1
#                     curSR = allSRList.get(i)
#                     if (not curSR.info.ephemeral) and (not na(curSR.info.breakTime)) and curSR.info.price == sr.info.price and ((sr.info.srType == "Resistance" and curSR.info.srType == "Support") or (sr.info.srType == "Support" and curSR.info.srType == "Resistance"))
#                         if curSR.breakFixed
#                             sr.info.startTime := curSR.info.breakTime
#                             sr.startFixed := true
#                         break

#     if not na(sr.info.breakTime)
#         if (not sr.breakFixed)
#             if sr.info.srType == "Resistance"
#                 sr.info.breakTime := findValRtnTime(barInfoList, sr.info.price, srInvalidation == "Wick" ? "High" : "Close", "Higher", sr.info.breakTime - srMS, sr.info.breakTime + srMS, sr.info.breakTime)
#             else
#                 sr.info.breakTime := findValRtnTime(barInfoList, sr.info.price, srInvalidation == "Wick" ? "Low" : "Close", "Lower", sr.info.breakTime - srMS, sr.info.breakTime + srMS, sr.info.breakTime)
#             sr.breakFixed := true
    
#     if sr.info.retestTimes.size() > 0 and fixRetests
#         for i = 0 to sr.info.retestTimes.size() - 1
#             curRetestTime = sr.info.retestTimes.get(i)

#             retestStartTime = curRetestTime - srMS
#             retestStartTime := math.max(retestStartTime, sr.info.startTime + 1)
            
#             retestEndTime = curRetestTime + srMS
#             if not na(sr.info.breakTime)
#                 retestEndTime := math.min(retestEndTime, sr.info.breakTime - 1)
            
#             if sr.info.srType == "Resistance"
#                 sr.info.retestTimes.set(i, findValRtnTime(barInfoList, sr.info.price, "High", "Higher", retestStartTime, retestEndTime, sr.info.retestTimes.get(i)))
#             else
#                 sr.info.retestTimes.set(i, findValRtnTime(barInfoList, sr.info.price, "Low", "Lower", retestStartTime, retestEndTime, sr.info.retestTimes.get(i)))

# getSR (srObj[] list, srPrice, eph, srType, timeframeStr) =>
#     srObj rtnSR = na
#     if list.size() > 0
#         for i = 0 to list.size() - 1
#             curSR = list.get(i)
#             if curSR.info.price == srPrice and curSR.info.ephemeral == eph and curSR.info.srType == srType and curSR.info.timeframeStr == timeframeStr
#                 rtnSR := curSR
#                 break
#     rtnSR

# // Handle SR
# handleTF (tfStr, tfEnabled) =>
#     if tfEnabled
#         tfSRInfoList = request.security(syminfo.tickerid, tfStr, allSRInfoList)
#         if not na(tfSRInfoList) and tfSRInfoList.size() > 0
#             for i = 0 to tfSRInfoList.size() - 1
#                 srInfo curSRInfo = tfSRInfoList.get(i)
#                 if fixSRs
#                     currentSameSR = getSR(allSRList, curSRInfo.price, curSRInfo.ephemeral, curSRInfo.srType, curSRInfo.timeframeStr)
#                     if not na(currentSameSR)
#                         if currentSameSR.startFixed
#                             curSRInfo.startTime := currentSameSR.info.startTime
#                         if currentSameSR.breakFixed
#                             curSRInfo.breakTime := currentSameSR.info.breakTime
#                         curSRInfo.retestTimes := currentSameSR.info.retestTimes
#                         // All other info should be replaced except fixed start, break and all retests.
#                         currentSameSR.info := curSRInfo
#                         if not currentSameSR.breakFixed
#                             fixSRToTimeframe(currentSameSR)
#                     else
#                         srObj newSRObj = srObj.new(curSRInfo)
#                         // We handle retests in current timeframe so no need to get them from upper.
#                         newSRObj.info.retestTimes := array.new<int>()
#                         newSRObj.retestLabels := array.new<label>()
#                         fixSRToTimeframe(newSRObj)
#                         allSRList.unshift(newSRObj)
#                 else
#                     srObj newSRObj = srObj.new(curSRInfo)
#                     newSRObj.retestLabels := array.new<label>()
#                     allSRList.unshift(newSRObj)
#     true

# if (bar_index > last_bar_index - maxDistanceToLastBar * 8) and barstate.isconfirmed
#     if not fixSRs
#         if allSRList.size() > 0
#             for i = 0 to allSRList.size() - 1
#                 srObj curSRObj = allSRList.get(i)
#                 safeDeleteSRObj(curSRObj)
#         allSRList.clear()
        
#     handleTF(timeframe1, timeframe1Enabled)
#     handleTF(timeframe2, timeframe2Enabled)
#     handleTF(timeframe3, timeframe3Enabled)
    
#     if allSRList.size() > 0
#         for i = 0 to allSRList.size() - 1
#             srObj curSRObj = allSRList.get(i)
#             safeDeleteSRObj(curSRObj)
#             tooClose = false
#             for j = 0 to allSRList.size() - 1
#                 closeSR = allSRList.get(j)
#                 if closeSR.rendered and math.abs(closeSR.info.price - curSRObj.info.price) <= tooCloseATR * atr and closeSR.info.srType == curSRObj.info.srType and closeSR.info.ephemeral == curSRObj.info.ephemeral
#                     tooClose := true
#                     if not str.contains((na(closeSR.combinedTimeframeStr) ? formatTimeframeString(closeSR.info.timeframeStr) : closeSR.combinedTimeframeStr), formatTimeframeString(curSRObj.info.timeframeStr))
#                         if na(closeSR.combinedTimeframeStr)
#                             closeSR.combinedTimeframeStr := formatTimeframeString(closeSR.info.timeframeStr) + " & " + formatTimeframeString(curSRObj.info.timeframeStr)
#                         else
#                             closeSR.combinedTimeframeStr += " & " + formatTimeframeString(curSRObj.info.timeframeStr)
#                     break
            
#             if (curSRObj.info.strength >= srStrength) and (na(curSRObj.info.breakTime) or (curSRObj.info.breakTime - curSRObj.info.startTime) >= minSRSize * curTFMS) and (not tooClose)
#                 renderSRObj(curSRObj)

# // Current Timeframe Retests
# if allSRList.size() > 0 and barstate.isconfirmed
#     for i = 0 to allSRList.size() - 1
#         srObj curSR = allSRList.get(i)
#         if na(curSR.info.breakTime) and time > curSR.info.startTime
#             if curSR.info.srType == "Resistance" and high >= curSR.info.price and close <= curSR.info.price
#                 int lastRetestTime = 0
#                 if curSR.info.retestTimes.size() > 0
#                     lastRetestTime := curSR.info.retestTimes.get(0)
                
#                 if lastRetestTime != time
#                     curSR.info.retestTimes.unshift(time)
            
#             else if curSR.info.srType == "Support" and low <= curSR.info.price and close >= curSR.info.price
#                 int lastRetestTime = 0
#                 if curSR.info.retestTimes.size() > 0
#                     lastRetestTime := curSR.info.retestTimes.get(0)
                
#                 if lastRetestTime != time
#                     curSR.info.retestTimes.unshift(time)

# //plotchar(alerts.get("Break") ? high : na, "", "✅", size = size.normal)
# //plotchar(alerts.get("Retest") ? high : na, "", "❤️", size = size.normal, location = location.belowbar)

# alertcondition(alerts.get("Retest"), "New Retest", "")
# alertcondition(alerts.get("Break"), "New Break", "")

# if enableRetestAlerts and alerts.get("Retest")
#     alert("New Retests Occured.")

# if enableBreakAlerts and alerts.get("Break")
#     alert("New Breaks Occured.")

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SRInfo:
    start_time: datetime
    price: float
    sr_type: str  # "Support" or "Resistance"
    strength: int
    timeframe_str: str
    ephemeral: bool = False
    break_time: Optional[datetime] = None
    retest_times: List[datetime] = None

    def __post_init__(self):
        if self.retest_times is None:
            self.retest_times = []

class SupportResistanceService:
    def __init__(self):
        self.SR_PIVOT_LENGTH = 15
        self.MAX_SR_INFO_LIST_SIZE = 10
        self.ATR_LENGTH = 20
        self.TOO_CLOSE_ATR = 1.0 / 8.0
        self.MIN_SR_SIZE = 5

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, length: int = None) -> pd.Series:
        """Calculate Average True Range"""
        if length is None:
            length = self.ATR_LENGTH
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=length).mean()

    def find_pivot_points(self, data: pd.DataFrame, length: int = None) -> Tuple[pd.Series, pd.Series]:
        """Find pivot high and low points"""
        if length is None:
            length = self.SR_PIVOT_LENGTH

        pivot_high = pd.Series(index=data.index, dtype=float)
        pivot_low = pd.Series(index=data.index, dtype=float)

        for i in range(length, len(data) - length):
            if all(data['high'].iloc[i] > data['high'].iloc[i-length:i]) and \
               all(data['high'].iloc[i] > data['high'].iloc[i+1:i+length+1]):
                pivot_high.iloc[i] = data['high'].iloc[i]

            if all(data['low'].iloc[i] < data['low'].iloc[i-length:i]) and \
               all(data['low'].iloc[i] < data['low'].iloc[i+1:i+length+1]):
                pivot_low.iloc[i] = data['low'].iloc[i]

        return pivot_high, pivot_low

    def get_support_resistance_levels(self, data: pd.DataFrame, timeframe: str = '1h') -> List[SRInfo]:
        """Calculate support and resistance levels"""
        # Calculate ATR
        atr = self.calculate_atr(data['high'], data['low'], data['close'])
        
        # Find pivot points
        pivot_high, pivot_low = self.find_pivot_points(data)
        
        sr_levels: List[SRInfo] = []
        
        # Process pivot lows (Support levels)
        for idx in pivot_low.dropna().index:
            price = pivot_low[idx]
            
            # Check if price is too close to existing levels
            too_close = False
            for sr in sr_levels:
                if abs(sr.price - price) < atr[idx] * self.TOO_CLOSE_ATR:
                    too_close = True
                    break
            
            if not too_close:
                sr_levels.append(SRInfo(
                    start_time=data['date'].iloc[idx],
                    price=price,
                    sr_type="Support",
                    strength=1,
                    timeframe_str=timeframe
                ))
        
        # Process pivot highs (Resistance levels)
        for idx in pivot_high.dropna().index:
            price = pivot_high[idx]
            
            # Check if price is too close to existing levels
            too_close = False
            for sr in sr_levels:
                if abs(sr.price - price) < atr[idx] * self.TOO_CLOSE_ATR:
                    too_close = True
                    break
            
            if not too_close:
                sr_levels.append(SRInfo(
                    start_time=data['date'].iloc[idx],
                    price=price,
                    sr_type="Resistance",
                    strength=1,
                    timeframe_str=timeframe
                ))

        # Sort levels by price
        sr_levels.sort(key=lambda x: x.price)
        
        return sr_levels

    def check_breaks_and_retests(self, data: pd.DataFrame, sr_levels: List[SRInfo]) -> List[SRInfo]:
        """Check for breaks and retests of support/resistance levels"""
        for sr in sr_levels:
            for idx, row in data.iterrows():
                current_time = row['date']
                if current_time <= sr.start_time:
                    continue
                    
                if sr.break_time is None:
                    # Check for breaks
                    if sr.sr_type == "Resistance" and row['high'] > sr.price:
                        sr.break_time = current_time
                    elif sr.sr_type == "Support" and row['low'] < sr.price:
                        sr.break_time = current_time
                
                # Check for retests
                if sr.break_time is None:
                    if sr.sr_type == "Resistance" and \
                       row['high'] >= sr.price and row['close'] <= sr.price:
                        if not sr.retest_times or sr.retest_times[-1] != current_time:
                            sr.retest_times.append(current_time)
                            sr.strength += 1
                    
                    elif sr.sr_type == "Support" and \
                         row['low'] <= sr.price and row['close'] >= sr.price:
                        if not sr.retest_times or sr.retest_times[-1] != current_time:
                            sr.retest_times.append(current_time)
                            sr.strength += 1
        
        return sr_levels

    def get_sr_levels(self, data: pd.DataFrame, timeframe: str = '1h') -> List[Dict]:
        """Main function to get support and resistance levels with breaks and retests"""
        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(data['date']):
            data['date'] = pd.to_datetime(data['date'])
            
        sr_levels = self.get_support_resistance_levels(data, timeframe)
        sr_levels = self.check_breaks_and_retests(data, sr_levels)
        
        # Convert to dict format for API response
        result = []
        for sr in sr_levels:
            # 确保所有时间都是有效的datetime对象
            if isinstance(sr.start_time, pd.Timestamp):
                start_time = sr.start_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                start_time = pd.to_datetime(sr.start_time).strftime('%Y-%m-%d %H:%M:%S')
                
            if sr.break_time is not None:
                if isinstance(sr.break_time, pd.Timestamp):
                    break_time = sr.break_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    break_time = pd.to_datetime(sr.break_time).strftime('%Y-%m-%d %H:%M:%S')
            else:
                break_time = None
                
            retest_times = []
            for rt in sr.retest_times:
                if isinstance(rt, pd.Timestamp):
                    retest_times.append(rt.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    retest_times.append(pd.to_datetime(rt).strftime('%Y-%m-%d %H:%M:%S'))
            
            result.append({
                'price': float(sr.price),
                'type': sr.sr_type,
                'strength': sr.strength,
                'start_time': start_time,
                'break_time': break_time,
                'retest_times': retest_times,
                'timeframe': sr.timeframe_str
            })
            
        return result