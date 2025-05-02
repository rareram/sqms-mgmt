Sub ExtractNonStandardCommitUsers()
    ' 인사DB 형식(이름(아이디))이 아닌 모든 commit_user 값을 추출하여 새 시트에 중복 제거 후 표시
    
    Dim ws As Worksheet
    Dim wsResult As Worksheet
    Dim lastRow As Long, lastCol As Long
    Dim i As Long, j As Long, resultRow As Long
    Dim cellValue As String
    Dim dict As Object
    Dim dictStandard As Object
    Dim header As String
    Dim commitUserCols As New Collection
    Dim patternType As String
    Dim extractReason As String
    
    ' 딕셔너리 객체 생성 (중복 제거용)
    Set dict = CreateObject("Scripting.Dictionary")
    dict.CompareMode = vbTextCompare ' 대소문자 구분 없이 비교
    
    ' 표준 형식 딕셔너리 (이미 매핑된 표준 형식 사용자 저장용)
    Set dictStandard = CreateObject("Scripting.Dictionary")
    dictStandard.CompareMode = vbTextCompare
    
    ' 현재 활성 시트 선택
    Set ws = ActiveSheet
    
    ' 데이터의 마지막 행과 열 찾기
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    
    ' commit_user로 시작하는 모든 컬럼 찾기
    For i = 1 To lastCol
        header = ws.Cells(1, i).Value
        If InStr(1, header, "commit_user", vbTextCompare) > 0 Then
            commitUserCols.Add i
        End If
    Next i
    
    ' commit_user 컬럼이 없으면 메시지 표시 후 종료
    If commitUserCols.Count = 0 Then
        MsgBox "commit_user로 시작하는 컬럼이 없습니다.", vbExclamation
        Exit Sub
    End If
    
    ' 새 결과 시트 생성 (이미 있으면 지우고 새로 생성)
    On Error Resume Next
    Application.DisplayAlerts = False
    Worksheets("비표준사용자").Delete
    Application.DisplayAlerts = True
    On Error GoTo 0
    
    Set wsResult = Worksheets.Add(After:=Worksheets(Worksheets.Count))
    wsResult.Name = "비표준사용자"
    
    ' 결과 시트에 헤더 추가
    wsResult.Cells(1, 1) = "추출된 사용자"
    wsResult.Cells(1, 2) = "패턴 유형"
    wsResult.Cells(1, 3) = "추출 사유"
    wsResult.Cells(1, 4) = "출처 컬럼"
    wsResult.Cells(1, 5) = "출처 행"
    
    ' 헤더 서식 지정
    With wsResult.Range("A1:E1")
        .Font.Bold = True
        .Interior.Color = RGB(200, 200, 200)
    End With
    
    ' 초기 결과 행 설정
    resultRow = 2
    
    ' 진행 상황 표시
    Application.ScreenUpdating = False
    Application.StatusBar = "데이터 검색 중..."
    
    ' 모든 commit_user 컬럼에서 비표준 형식 찾기
    For Each colIndex In commitUserCols
        For i = 2 To lastRow  ' 첫 번째 행은 헤더라고 가정
            cellValue = Trim(ws.Cells(i, colIndex).Value)
            
            ' 빈 셀이 아닌 경우만 처리
            If Len(cellValue) > 0 Then
                patternType = ""
                extractReason = ""
                
                ' 표준 형식인지 확인: 이름(아이디) 패턴 검사
                If IsStandardFormat(cellValue) Then
                    ' 표준 형식이면 딕셔너리에 추가만 하고 추출하지 않음
                    If Not dictStandard.Exists(cellValue) Then
                        dictStandard.Add cellValue, 1
                    End If
                Else
                    ' 비표준 형식: 패턴 분석
                    AnalyzeNonStandardPattern cellValue, patternType, extractReason
                    
                    ' 중복 체크 및 추가
                    If Not dict.Exists(cellValue) Then
                        dict.Add cellValue, patternType & "|" & extractReason
                        
                        ' 결과 시트에 추가
                        wsResult.Cells(resultRow, 1) = cellValue
                        wsResult.Cells(resultRow, 2) = patternType
                        wsResult.Cells(resultRow, 3) = extractReason
                        wsResult.Cells(resultRow, 4) = ws.Cells(1, colIndex).Value
                        wsResult.Cells(resultRow, 5) = i
                        resultRow = resultRow + 1
                    End If
                End If
            End If
        Next i
        
        ' 진행 상황 업데이트
        Application.StatusBar = "처리 중: " & colIndex & "/" & lastCol & " 컬럼 완료"
    Next colIndex
    
    ' 결과 요약
    wsResult.Cells(resultRow + 1, 1) = "총 " & dict.Count & "개의 비표준 형식 사용자가 추출되었습니다."
    wsResult.Cells(resultRow + 1, 2) = "표준 형식 사용자: " & dictStandard.Count & "개"
    wsResult.Cells(resultRow + 1, 1).Font.Bold = True
    wsResult.Cells(resultRow + 1, 2).Font.Bold = True
    
    ' 컬럼 자동 맞춤
    wsResult.Columns("A:E").AutoFit
    
    ' 매핑 템플릿 추가
    wsResult.Cells(resultRow + 3, 1) = "매핑 템플릿:"
    wsResult.Cells(resultRow + 3, 1).Font.Bold = True
    
    wsResult.Cells(resultRow + 4, 1) = "AS-IS"
    wsResult.Cells(resultRow + 4, 2) = "TO-BE"
    wsResult.Cells(resultRow + 4, 3) = "비고"
    
    With wsResult.Range(wsResult.Cells(resultRow + 4, 1), wsResult.Cells(resultRow + 4, 3))
        .Font.Bold = True
        .Interior.Color = RGB(200, 200, 200)
    End With
    
    ' 추출된 사용자를 매핑 템플릿에 추가
    Dim mapRow As Long
    mapRow = resultRow + 5
    
    ' 키와 값을 함께 가져와서 정렬을 위한 배열로 저장
    Dim sortData() As String
    Dim key As Variant
    Dim idx As Long
    
    ReDim sortData(dict.Count - 1, 2) ' 0부터 시작하는 인덱스
    
    idx = 0
    For Each key In dict.Keys
        sortData(idx, 0) = key
        sortData(idx, 1) = dict(key)
        idx = idx + 1
    Next key
    
    ' 패턴 유형별로 정렬
    Call SortByPatternType(sortData)
    
    ' 정렬된 데이터를 시트에 출력
    For i = 0 To UBound(sortData)
        wsResult.Cells(mapRow, 1) = sortData(i, 0)
        
        ' 패턴 정보를 비고에 추가
        Dim patternInfo As String
        patternInfo = Split(sortData(i, 1), "|")(0) ' 패턴 유형
        
        wsResult.Cells(mapRow, 3) = patternInfo
        mapRow = mapRow + 1
    Next i
    
    ' 매핑 템플릿 컬럼 자동 맞춤
    wsResult.Columns("A:C").AutoFit
    
    ' 상태 표시줄 초기화 및 화면 업데이트 다시 활성화
    Application.StatusBar = False
    Application.ScreenUpdating = True
    
    ' 결과 시트 활성화
    wsResult.Activate
    
    ' 완료 메시지
    MsgBox "추출 완료: " & dict.Count & "개의 비표준 형식 사용자가 추출되었습니다." & vbCrLf & _
           "표준 형식 사용자: " & dictStandard.Count & "개" & vbCrLf & _
           "결과는 '비표준사용자' 시트에 있습니다.", vbInformation
           
End Sub

Function IsStandardFormat(value As String) As Boolean
    ' 표준 형식인지 확인: 이름(아이디) 패턴
    ' 예: 홍길동(sksdu_1234), 김철수(test@example.com)
    
    Dim regEx As Object
    Set regEx = CreateObject("VBScript.RegExp")
    
    ' 패턴: 한글/영문 이름 + 괄호 + 내용 + 괄호닫기
    ' 한글이름(영문/숫자/특수문자)
    regEx.Pattern = "^[\w\s가-힣]+" & "\(" & "[\w\.\@\-\_]+" & "\)" & "$"
    regEx.Global = False
    
    IsStandardFormat = regEx.Test(value)
End Function

Sub AnalyzeNonStandardPattern(value As String, ByRef patternType As String, ByRef reason As String)
    ' 비표준 형식의 패턴을 분석하고 유형과 사유를 반환
    
    ' 이메일 주소 형식인지 확인
    If IsEmailFormat(value) Then
        patternType = "이메일"
        reason = "이메일 주소만 있음"
        Exit Sub
    End If
    
    ' sksdu_ 형식인지 확인
    If InStr(1, value, "sksdu_", vbTextCompare) > 0 Then
        patternType = "사번ID"
        reason = "사번ID만 있음"
        Exit Sub
    End If
    
    ' 도메인 슬래시 형식 (ADTKOREA\사용자)
    If InStr(1, value, "\") > 0 Then
        patternType = "도메인계정"
        reason = "도메인\사용자 형식"
        Exit Sub
    End If
    
    ' 한글 이름만 있는 경우
    If IsKoreanNameOnly(value) Then
        patternType = "이름만"
        reason = "한글 이름만 있음"
        Exit Sub
    End If
    
    ' 영문 이름만 있는 경우
    If IsEnglishNameOnly(value) Then
        patternType = "영문이름"
        reason = "영문 이름만 있음"
        Exit Sub
    End If
    
    ' 기타 알 수 없는 형식
    patternType = "기타"
    reason = "알 수 없는 형식"
End Sub

Function IsEmailFormat(value As String) As Boolean
    ' 이메일 형식인지 확인
    Dim regEx As Object
    Set regEx = CreateObject("VBScript.RegExp")
    
    regEx.Pattern = "^[\w\-\.]+@[\w\-\.]+\.[a-zA-Z]{2,}$"
    regEx.Global = False
    
    IsEmailFormat = regEx.Test(value)
End Function

Function IsKoreanNameOnly(value As String) As Boolean
    ' 한글 이름만 있는지 확인 (2-5자 한글)
    Dim regEx As Object
    Set regEx = CreateObject("VBScript.RegExp")
    
    regEx.Pattern = "^[가-힣]{2,5}$"
    regEx.Global = False
    
    IsKoreanNameOnly = regEx.Test(value)
End Function

Function IsEnglishNameOnly(value As String) As Boolean
    ' 영문 이름만 있는지 확인
    Dim regEx As Object
    Set regEx = CreateObject("VBScript.RegExp")
    
    regEx.Pattern = "^[a-zA-Z\s]{2,30}$"
    regEx.Global = False
    
    IsEnglishNameOnly = regEx.Test(value)
End Function

Sub SortByPatternType(ByRef arr() As String)
    ' 패턴 유형별로 정렬
    Dim i As Long, j As Long
    Dim tempKey As String, tempValue As String
    
    For i = LBound(arr) To UBound(arr) - 1
        For j = i + 1 To UBound(arr)
            ' 패턴 유형 비교
            Dim patternI As String, patternJ As String
            patternI = Split(arr(i, 1), "|")(0)
            patternJ = Split(arr(j, 1), "|")(0)
            
            If patternI > patternJ Then
                ' 교환
                tempKey = arr(i, 0)
                tempValue = arr(i, 1)
                arr(i, 0) = arr(j, 0)
                arr(i, 1) = arr(j, 1)
                arr(j, 0) = tempKey
                arr(j, 1) = tempValue
            End If
        Next j
    Next i
End Sub

Sub ExportNonStandardUsersToCSV()
    ' 추출된 비표준 사용자 매핑 템플릿을 CSV 파일로 내보내기
    
    Dim wsResult As Worksheet
    Dim lastRow As Long
    Dim filePath As String
    Dim startRow As Long
    Dim i As Long
    
    ' 결과 시트 확인
    On Error Resume Next
    Set wsResult = Worksheets("비표준사용자")
    On Error GoTo 0
    
    If wsResult Is Nothing Then
        MsgBox "비표준사용자 시트가 없습니다. 먼저 ExtractNonStandardCommitUsers를 실행하세요.", vbExclamation
        Exit Sub
    End If
    
    ' 매핑 템플릿 시작 행 찾기
    startRow = 1
    Do While startRow < 1000
        If wsResult.Cells(startRow, 1).Value = "매핑 템플릿:" Then
            startRow = startRow + 1
            Exit Do
        End If
        startRow = startRow + 1
    Loop
    
    If startRow >= 1000 Then
        MsgBox "매핑 템플릿을 찾을 수 없습니다.", vbExclamation
        Exit Sub
    End If
    
    ' CSV 파일 저장 경로 설정
    filePath = Application.DefaultFilePath & "\commit_user_mapping.csv"
    
    ' 다른 경로로 저장할지 묻기
    Dim result As VbMsgBoxResult
    result = MsgBox("매핑 템플릿을 다음 경로에 CSV로 저장합니다:" & vbCrLf & filePath & vbCrLf & vbCrLf & _
                   "다른 경로로 저장하시겠습니까?", vbYesNo + vbQuestion)
                   
    If result = vbYes Then
        ' 파일 대화상자 표시
        Dim dlgSave As FileDialog
        Set dlgSave = Application.FileDialog(msoFileDialogSaveAs)
        
        With dlgSave
            .InitialFileName = "commit_user_mapping.csv"
            .Title = "매핑 템플릿 저장"
            .ButtonName = "저장"
            .Filters.Clear
            .Filters.Add "CSV 파일", "*.csv"
            
            If .Show = True Then
                filePath = .SelectedItems(1)
            Else
                MsgBox "저장이 취소되었습니다.", vbInformation
                Exit Sub
            End If
        End With
    End If
    
    ' 매핑 템플릿 끝 찾기
    lastRow = startRow
    Do While wsResult.Cells(lastRow + 1, 1).Value <> ""
        lastRow = lastRow + 1
    Loop
    
    ' CSV 파일로 저장
    Dim fso As Object
    Dim ts As Object
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set ts = fso.CreateTextFile(filePath, True)
    
    ' 헤더 쓰기
    ts.WriteLine "AS-IS,TO-BE,비고"
    
    ' 데이터 쓰기
    For i = startRow + 1 To lastRow
        Dim asIs As String, toBe As String, note As String
        
        asIs = wsResult.Cells(i, 1).Value
        toBe = wsResult.Cells(i, 2).Value
        note = wsResult.Cells(i, 3).Value
        
        ' 특수 문자 처리
        asIs = Replace(asIs, """", """""")  ' 큰따옴표 이스케이프
        toBe = Replace(toBe, """", """""")
        note = Replace(note, """", """""")
        
        ' 콤마가 포함된 경우 따옴표로 감싸기
        If InStr(1, asIs, ",") > 0 Then asIs = """" & asIs & """"
        If InStr(1, toBe, ",") > 0 Then toBe = """" & toBe & """"
        If InStr(1, note, ",") > 0 Then note = """" & note & """"
        
        ts.WriteLine asIs & "," & toBe & "," & note
    Next i
    
    ts.Close
    
    MsgBox "매핑 템플릿이 다음 경로에 저장되었습니다:" & vbCrLf & filePath, vbInformation
    
End Sub

Sub AnalyzeCommitUserPatterns()
    ' 커밋 사용자 패턴을 분석하여 통계 정보를 제공
    
    Dim ws As Worksheet
    Dim wsStats As Worksheet
    Dim lastRow As Long, lastCol As Long
    Dim i As Long, j As Long
    Dim cellValue As String
    Dim dictPatterns As Object
    Dim commitUserCols As New Collection
    Dim header As String
    Dim patternType As String
    Dim extractReason As String
    Dim totalCells As Long
    Dim validCells As Long
    
    ' 패턴 통계용 딕셔너리
    Set dictPatterns = CreateObject("Scripting.Dictionary")
    dictPatterns.CompareMode = vbTextCompare
    
    ' 현재 활성 시트 선택
    Set ws = ActiveSheet
    
    ' 데이터의 마지막 행과 열 찾기
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    
    ' commit_user로 시작하는 모든 컬럼 찾기
    For i = 1 To lastCol
        header = ws.Cells(1, i).Value
        If InStr(1, header, "commit_user", vbTextCompare) > 0 Then
            commitUserCols.Add i
        End If
    Next i
    
    ' commit_user 컬럼이 없으면 메시지 표시 후 종료
    If commitUserCols.Count = 0 Then
        MsgBox "commit_user로 시작하는 컬럼이 없습니다.", vbExclamation
        Exit Sub
    End If
    
    ' 새 통계 시트 생성
    On Error Resume Next
    Application.DisplayAlerts = False
    Worksheets("커밋패턴분석").Delete
    Application.DisplayAlerts = True
    On Error GoTo 0
    
    Set wsStats = Worksheets.Add(After:=Worksheets(Worksheets.Count))
    wsStats.Name = "커밋패턴분석"
    
    ' 결과 시트에 헤더 추가
    wsStats.Cells(1, 1) = "패턴 유형"
    wsStats.Cells(1, 2) = "개수"
    wsStats.Cells(1, 3) = "비율(%)"
    wsStats.Cells(1, 4) = "설명"
    
    ' 헤더 서식 지정
    With wsStats.Range("A1:D1")
        .Font.Bold = True
        .Interior.Color = RGB(200, 200, 200)
    End With
    
    ' 진행 상황 표시
    Application.ScreenUpdating = False
    Application.StatusBar = "패턴 분석 중..."
    
    ' 초기 카운터
    dictPatterns.Add "표준형식", 0
    dictPatterns.Add "이메일", 0
    dictPatterns.Add "사번ID", 0
    dictPatterns.Add "도메인계정", 0
    dictPatterns.Add "이름만", 0
    dictPatterns.Add "영문이름", 0
    dictPatterns.Add "기타", 0
    dictPatterns.Add "빈셀", 0
    
    totalCells = 0
    validCells = 0
    
    ' 모든 commit_user 컬럼 분석
    For Each colIndex In commitUserCols
        For i = 2 To lastRow  ' 첫 번째 행은 헤더라고 가정
            totalCells = totalCells + 1
            
            cellValue = Trim(ws.Cells(i, colIndex).Value)
            
            ' 빈 셀인 경우
            If Len(cellValue) = 0 Then
                dictPatterns("빈셀") = dictPatterns("빈셀") + 1
            Else
                validCells = validCells + 1
                
                ' 표준 형식인지 확인
                If IsStandardFormat(cellValue) Then
                    dictPatterns("표준형식") = dictPatterns("표준형식") + 1
                Else
                    ' 비표준 형식: 패턴 분석
                    AnalyzeNonStandardPattern cellValue, patternType, extractReason
                    dictPatterns(patternType) = dictPatterns(patternType) + 1
                End If
            End If
        Next i
        
        ' 진행 상황 업데이트
        Application.StatusBar = "패턴 분석 중: " & colIndex & "/" & lastCol & " 컬럼 완료"
    Next colIndex
    
    ' 통계 결과 기록
    Dim rowIndex As Long
    rowIndex = 2
    
    Dim keys As Variant
    keys = Array("표준형식", "이메일", "사번ID", "도메인계정", "이름만", "영문이름", "기타", "빈셀")
    
    Dim descriptions As Variant
    descriptions = Array( _
        "올바른 형식: 이름(아이디)", _
        "이메일 주소만 있음", _
        "사번ID(sksdu_)만 있음", _
        "도메인\사용자 형식", _
        "한글 이름만 있음", _
        "영문 이름만 있음", _
        "기타 알 수 없는 형식", _
        "데이터 없음" _
    )
    
    ' 통계 작성
    For i = 0 To UBound(keys)
        Dim count As Long
        Dim percentage As Double
        
        count = dictPatterns(keys(i))
        
        If validCells > 0 And keys(i) <> "빈셀" Then
            percentage = count / validCells * 100
        ElseIf keys(i) = "빈셀" Then
            percentage = count / totalCells * 100
        Else
            percentage = 0
        End If
        
        wsStats.Cells(rowIndex, 1) = keys(i)
        wsStats.Cells(rowIndex, 2) = count
        wsStats.Cells(rowIndex, 3) = Format(percentage, "0.00") & "%"
        wsStats.Cells(rowIndex, 4) = descriptions(i)
        
        rowIndex = rowIndex + 1
    Next i
    
    ' 요약 정보 추가
    wsStats.Cells(rowIndex + 1, 1) = "요약 정보"
    wsStats.Cells(rowIndex + 1, 1).Font.Bold = True
    
    wsStats.Cells(rowIndex + 2, 1) = "전체 셀 수"
    wsStats.Cells(rowIndex + 2, 2) = totalCells
    
    wsStats.Cells(rowIndex + 3, 1) = "데이터 있는 셀 수"
    wsStats.Cells(rowIndex + 3, 2) = validCells
    wsStats.Cells(rowIndex + 3, 3) = Format(validCells / totalCells * 100, "0.00") & "%"
    
    wsStats.Cells(rowIndex + 4, 1) = "표준 형식 비율"
    wsStats.Cells(rowIndex + 4, 2) = dictPatterns("표준형식")
    wsStats.Cells(rowIndex + 4, 3) = Format(dictPatterns("표준형식") / validCells * 100, "0.00") & "%"
    
    wsStats.Cells(rowIndex + 5, 1) = "비표준 형식 비율"
    wsStats.Cells(rowIndex + 5, 2) = validCells - dictPatterns("표준형식")
    wsStats.Cells(rowIndex + 5, 3) = Format((validCells - dictPatterns("표준형식")) / validCells * 100, "0.00") & "%"
    
    ' 컬럼 자동 맞춤
    wsStats.Columns("A:D").AutoFit
    
    ' 차트 추가 (패턴 분포 원형 차트)
    Dim chartObj As ChartObject
    Dim chartData As Range
    
    ' 차트 데이터 범위 설정 (빈셀 제외)
    Set chartData = wsStats.Range(wsStats.Cells(2, 1), wsStats.Cells(8, 2))
    
    ' 차트 생성
    Set chartObj = wsStats.ChartObjects.Add( _
        Left:=wsStats.Columns("F").Left, _
        Top:=wsStats.Rows(2).Top, _
        Width:=300, _
        Height:=200)
    
    With chartObj.Chart
        .SetSourceData Source:=chartData
        .ChartType = xlPie
        .HasTitle = True
        .ChartTitle.Text = "커밋 사용자 패턴 분포"
        .ApplyLayout 3 ' 레이아웃 적용
        .HasLegend = True
        .Legend.Position = xlLegendPositionRight
    End With
    
    ' 상태 표시줄 초기화 및 화면 업데이트 다시 활성화
    Application.StatusBar = False
    Application.ScreenUpdating = True
    
    ' 결과 시트 활성화
    wsStats.Activate
    
    ' 완료 메시지
    MsgBox "패턴 분석 완료!" & vbCrLf & _
           "전체 셀: " & totalCells & "개" & vbCrLf & _
           "데이터 있는 셀: " & validCells & "개" & vbCrLf & _
           "표준 형식: " & dictPatterns("표준형식") & "개 (" & Format(dictPatterns("표준형식") / validCells * 100, "0.00") & "%)" & vbCrLf & _
           "비표준 형식: " & (validCells - dictPatterns("표준형식")) & "개 (" & Format((validCells - dictPatterns("표준형식")) / validCells * 100, "0.00") & "%)"
           
End Sub

' 원래 함수도 유지 (키워드 추출용)
Sub ExtractCommitUsersWithKeyword()
    ' 비표준 형식의 커밋 사용자 값을 추출하여 새 시트에 중복 제거 후 표시
    
    Dim ws As Worksheet
    Dim wsResult As Worksheet
    Dim lastRow As Long, lastCol As Long
    Dim i As Long, j As Long, resultRow As Long
    Dim cellValue As String
    Dim dict As Object
    Dim header As String
    Dim commitUserCols As New Collection
    Dim keyword As String
    
    ' 검색 키워드 설정 (공백일 경우 모든 비표준 형식 대상)
    keyword = InputBox("추출할 특정 키워드를 입력하세요 (공백 입력시 모든 비표준 형식 추출):", "키워드 입력", "sksdu_")
    
    ' 딕셔너리 객체 생성 (중복 제거용)
    Set dict = CreateObject("Scripting.Dictionary")
    dict.CompareMode = vbTextCompare ' 대소문자 구분 없이 비교
    
    ' 현재 활성 시트 선택
    Set ws = ActiveSheet
    
    ' 데이터의 마지막 행과 열 찾기
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    
    ' commit_user로 시작하는 모든 컬럼 찾기
    For i = 1 To lastCol
        header = ws.Cells(1, i).Value
        If InStr(1, header, "commit_user", vbTextCompare) > 0 Then
            commitUserCols.Add i
        End If
    Next i
    
    ' commit_user 컬럼이 없으면 메시지 표시 후 종료
    If commitUserCols.Count = 0 Then
        MsgBox "commit_user로 시작하는 컬럼이 없습니다.", vbExclamation
        Exit Sub
    End If
    
    ' 새 결과 시트 생성 (이미 있으면 지우고 새로 생성)
    On Error Resume Next
    Application.DisplayAlerts = False
    Worksheets("추출된사용자").Delete
    Application.DisplayAlerts = True
    On Error GoTo 0
    
    Set wsResult = Worksheets.Add(After:=Worksheets(Worksheets.Count))
    wsResult.Name = "추출된사용자"
    
    ' 결과 시트에 헤더 추가
    wsResult.Cells(1, 1) = "추출된 사용자"
    wsResult.Cells(1, 2) = "패턴 유형"
    wsResult.Cells(1, 3) = "출처 컬럼"
    wsResult.Cells(1, 4) = "출처 행"
    
    ' 헤더 서식 지정
    With wsResult.Range("A1:D1")
        .Font.Bold = True
        .Interior.Color = RGB(200, 200, 200)
    End With
    
    ' 초기 결과 행 설정
    resultRow = 2
    
    ' 진행 상황 표시
    Application.ScreenUpdating = False
    Application.StatusBar = "데이터 검색 중..."
    
    ' 모든 commit_user 컬럼에서 키워드 혹은 비표준 형식 검색
    For Each colIndex In commitUserCols
        For i = 2 To lastRow  ' 첫 번째 행은 헤더라고 가정
            cellValue = ws.Cells(i, colIndex).Value
            
            ' 셀이 비어있지 않은 경우
            If Len(cellValue) > 0 Then
                ' 키워드가 지정된 경우 해당 키워드만 검색
                If keyword <> "" Then
                    If InStr(1, cellValue, keyword, vbTextCompare) > 0 Then
                        ' 중복 체크 및 추가
                        If Not dict.Exists(cellValue) Then
                            dict.Add cellValue, "키워드: " & keyword
                            
                            ' 결과 시트에 추가
                            wsResult.Cells(resultRow, 1) = cellValue
                            wsResult.Cells(resultRow, 2) = "키워드 포함: " & keyword
                            wsResult.Cells(resultRow, 3) = ws.Cells(1, colIndex).Value
                            wsResult.Cells(resultRow, 4) = i
                            resultRow = resultRow + 1
                        End If
                    End If
                ' 키워드가 지정되지 않은 경우 표준 형식이 아닌 것만 추출
                Else
                    If Not IsStandardFormat(cellValue) Then
                        ' 패턴 분석
                        Dim patternType As String
                        patternType = AnalyzePattern(cellValue)
                        
                        ' 중복 체크 및 추가
                        If Not dict.Exists(cellValue) Then
                            dict.Add cellValue, patternType
                            
                            ' 결과 시트에 추가
                            wsResult.Cells(resultRow, 1) = cellValue
                            wsResult.Cells(resultRow, 2) = patternType
                            wsResult.Cells(resultRow, 3) = ws.Cells(1, colIndex).Value
                            wsResult.Cells(resultRow, 4) = i
                            resultRow = resultRow + 1
                        End If
                    End If
                End If
            End If
        Next i
        
        ' 진행 상황 업데이트
        Application.StatusBar = "처리 중: " & colIndex & "/" & lastCol & " 컬럼 완료"
    Next colIndex
    
    ' 결과 요약
    wsResult.Cells(resultRow + 1, 1) = "총 " & dict.Count & "개의 사용자 ID가 추출되었습니다."
    wsResult.Cells(resultRow + 1, 1).Font.Bold = True
    
    ' 컬럼 자동 맞춤
    wsResult.Columns("A:D").AutoFit
    
    ' 매핑 템플릿 추가
    wsResult.Cells(resultRow + 3, 1) = "매핑 템플릿:"
    wsResult.Cells(resultRow + 3, 1).Font.Bold = True
    
    wsResult.Cells(resultRow + 4, 1) = "AS-IS"
    wsResult.Cells(resultRow + 4, 2) = "TO-BE"
    wsResult.Cells(resultRow + 4, 3) = "비고"
    
    With wsResult.Range(wsResult.Cells(resultRow + 4, 1), wsResult.Cells(resultRow + 4, 3))
        .Font.Bold = True
        .Interior.Color = RGB(200, 200, 200)
    End With
    
    ' 추출된 사용자를 매핑 템플릿에 추가
    Dim mapRow As Long
    mapRow = resultRow + 5
    
    ' 패턴별 정렬을 위한 배열 생성
    Dim sortArray() As Variant
    ReDim sortArray(dict.Count - 1, 2)
    
    ' 배열에 데이터 채우기
    Dim k As Long
    k = 0
    For Each key In dict.Keys
        sortArray(k, 0) = key
        sortArray(k, 1) = dict(key)
        k = k + 1
    Next key
    
    ' 패턴별로 정렬
    Call SortByPattern(sortArray)
    
    ' 정렬된 데이터 출력
    For i = 0 To UBound(sortArray)
        wsResult.Cells(mapRow, 1) = sortArray(i, 0)
        wsResult.Cells(mapRow, 3) = sortArray(i, 1)
        mapRow = mapRow + 1
    Next i
    
    ' 매핑 템플릿 컬럼 자동 맞춤
    wsResult.Columns("A:C").AutoFit
    
    ' 상태 표시줄 초기화 및 화면 업데이트 다시 활성화
    Application.StatusBar = False
    Application.ScreenUpdating = True
    
    ' 결과 시트 활성화
    wsResult.Activate
    
    ' 완료 메시지
    MsgBox "추출 완료: " & dict.Count & "개의 사용자 ID가 추출되었습니다." & vbCrLf & _
           "결과는 '추출된사용자' 시트에 있습니다.", vbInformation
           
End Sub

Function IsStandardFormat(value As String) As Boolean
    ' 표준 형식인지 확인: 이름(아이디) 패턴
    ' 예: 홍길동(sksdu_1234), 김철수(test@example.com)
    
    ' 빈 문자열 체크
    If value = "" Then
        IsStandardFormat = False
        Exit Function
    End If
    
    Dim regEx As Object
    Set regEx = CreateObject("VBScript.RegExp")
    
    ' 패턴: 한글/영문 이름 + 괄호 + 내용 + 괄호닫기
    ' 한글이름(영문/숫자/특수문자)
    regEx.Pattern = "^[\w\s가-힣]+" & "\(" & "[\w\.\@\-\_]+" & "\)" & "$"
    regEx.Global = False
    
    IsStandardFormat = regEx.Test(value)
End Function

Function AnalyzePattern(value As String) As String
    ' 비표준 형식의 패턴을 분석하고 유형을 반환
    
    ' 빈 문자열 체크
    If value = "" Then
        AnalyzePattern = "빈 값"
        Exit Function
    End If
    
    ' 이메일 주소 형식인지 확인
    If IsEmailFormat(value) Then
        AnalyzePattern = "이메일"
        Exit Function
    End If
    
    ' sksdu_ 형식인지 확인
    If InStr(1, value, "sksdu_", vbTextCompare) > 0 Then
        AnalyzePattern = "사번ID"
        Exit Function
    End If
    
    ' 도메인 슬래시 형식 (ADTKOREA\사용자)
    If InStr(1, value, "\") > 0 Then
        AnalyzePattern = "도메인계정"
        Exit Function
    End If
    
    ' 한글 이름만 있는 경우
    If IsKoreanNameOnly(value) Then
        AnalyzePattern = "한글이름만"
        Exit Function
    End If
    
    ' 영문 이름만 있는 경우
    If IsEnglishNameOnly(value) Then
        AnalyzePattern = "영문이름만"
        Exit Function
    End If
    
    ' 기타 알 수 없는 형식
    AnalyzePattern = "기타"
End Function

Function IsEmailFormat(value As String) As Boolean
    ' 이메일 형식인지 확인
    Dim regEx As Object
    Set regEx = CreateObject("VBScript.RegExp")
    
    regEx.Pattern = "^[\w\-\.]+@[\w\-\.]+\.[a-zA-Z]{2,}$"
    regEx.Global = False
    
    IsEmailFormat = regEx.Test(value)
End Function

Function IsKoreanNameOnly(value As String) As Boolean
    ' 한글 이름만 있는지 확인 (2-5자 한글)
    Dim regEx As Object
    Set regEx = CreateObject("VBScript.RegExp")
    
    regEx.Pattern = "^[가-힣]{2,5}$"
    regEx.Global = False
    
    IsKoreanNameOnly = regEx.Test(value)
End Function

Function IsEnglishNameOnly(value As String) As Boolean
    ' 영문 이름만 있는지 확인
    Dim regEx As Object
    Set regEx = CreateObject("VBScript.RegExp")
    
    regEx.Pattern = "^[a-zA-Z\s]{2,30}$"
    regEx.Global = False
    
    IsEnglishNameOnly = regEx.Test(value)
End Function

Sub SortByPattern(ByRef arr() As Variant)
    ' 패턴 유형별로 정렬
    Dim i As Long, j As Long
    Dim tempKey As String, tempVal As String
    
    For i = 0 To UBound(arr) - 1
        For j = i + 1 To UBound(arr)
            If CStr(arr(i, 1)) > CStr(arr(j, 1)) Then
                ' 교환
                tempKey = arr(i, 0)
                tempVal = arr(i, 1)
                arr(i, 0) = arr(j, 0)
                arr(i, 1) = arr(j, 1)
                arr(j, 0) = tempKey
                arr(j, 1) = tempVal
            End If
        Next j
    Next i
End Sub

Sub ExportToCSV()
    ' 추출된 사용자 매핑 템플릿을 CSV 파일로 내보내기
    
    Dim wsResult As Worksheet
    Dim lastRow As Long
    Dim filePath As String
    Dim startRow As Long
    Dim i As Long
    
    ' 결과 시트 확인
    On Error Resume Next
    Set wsResult = Worksheets("추출된사용자")
    On Error GoTo 0
    
    If wsResult Is Nothing Then
        MsgBox "추출된사용자 시트가 없습니다. 먼저 ExtractCommitUsersWithKeyword를 실행하세요.", vbExclamation
        Exit Sub
    End If
    
    ' 매핑 템플릿 시작 행 찾기
    startRow = 1
    Do While startRow < 1000
        If wsResult.Cells(startRow, 1).Value = "매핑 템플릿:" Then
            startRow = startRow + 1
            Exit Do
        End If
        startRow = startRow + 1
    Loop
    
    If startRow >= 1000 Then
        MsgBox "매핑 템플릿을 찾을 수 없습니다.", vbExclamation
        Exit Sub
    End If
    
    ' CSV 파일 저장 경로 설정
    filePath = Application.DefaultFilePath & "\commit_user_mapping.csv"
    
    ' 다른 경로로 저장할지 묻기
    Dim result As VbMsgBoxResult
    result = MsgBox("매핑 템플릿을 다음 경로에 CSV로 저장합니다:" & vbCrLf & filePath & vbCrLf & vbCrLf & _
                   "다른 경로로 저장하시겠습니까?", vbYesNo + vbQuestion)
                   
    If result = vbYes Then
        ' 파일 대화상자 표시
        Dim dlgSave As FileDialog
        Set dlgSave = Application.FileDialog(msoFileDialogSaveAs)
        
        With dlgSave
            .InitialFileName = "commit_user_mapping.csv"
            .Title = "매핑 템플릿 저장"
            .ButtonName = "저장"
            .Filters.Clear
            .Filters.Add "CSV 파일", "*.csv"
            
            If .Show = True Then
                filePath = .SelectedItems(1)
            Else
                MsgBox "저장이 취소되었습니다.", vbInformation
                Exit Sub
            End If
        End With
    End If
    
    ' 매핑 템플릿 끝 찾기
    lastRow = startRow
    Do While lastRow < wsResult.Rows.Count
        If wsResult.Cells(lastRow + 1, 1).Value = "" Then
            Exit Do
        End If
        lastRow = lastRow + 1
    Loop
    
    ' CSV 파일로 저장
    Dim fso As Object
    Dim ts As Object
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set ts = fso.CreateTextFile(filePath, True)
    
    ' 헤더 쓰기
    ts.WriteLine "AS-IS,TO-BE,비고"
    
    ' 데이터 쓰기
    For i = startRow + 1 To lastRow
        Dim asIs As String, toBe As String, note As String
        
        asIs = wsResult.Cells(i, 1).Value
        toBe = wsResult.Cells(i, 2).Value
        note = wsResult.Cells(i, 3).Value
        
        ' 특수 문자 처리
        asIs = Replace(asIs, """", """""")  ' 큰따옴표 이스케이프
        toBe = Replace(toBe, """", """""")
        note = Replace(note, """", """""")
        
        ' 콤마가 포함된 경우 따옴표로 감싸기
        If InStr(1, asIs, ",") > 0 Then asIs = """" & asIs & """"
        If InStr(1, toBe, ",") > 0 Then toBe = """" & toBe & """"
        If InStr(1, note, ",") > 0 Then note = """" & note & """"
        
        ts.WriteLine asIs & "," & toBe & "," & note
    Next i
    
    ts.Close
    
    MsgBox "매핑 템플릿이 다음 경로에 저장되었습니다:" & vbCrLf & filePath, vbInformation
    
End Sub

Sub CreateRibbonMenu()
    ' 엑셀 리본 메뉴에 추가할 수 있는 메뉴 생성
    ' 이 함수는 워크북 수준에서 실행해야 합니다
    
    On Error Resume Next
    ' 기존 명령 버튼이 있다면 삭제
    Application.CommandBars("Worksheet Menu Bar").Controls("커밋사용자관리").Delete
    On Error GoTo 0
    
    ' 새 메뉴 항목 추가
    Dim menuBar As CommandBar
    Dim newMenu As CommandBarControl
    Dim menuItem As CommandBarButton
    
    Set menuBar = Application.CommandBars("Worksheet Menu Bar")
    Set newMenu = menuBar.Controls.Add(Type:=msoControlPopup, Temporary:=True)
    
    newMenu.Caption = "커밋사용자관리"
    
    ' 키워드로 사용자 추출
    Set menuItem = newMenu.Controls.Add(Type:=msoControlButton, Temporary:=True)
    With menuItem
        .Caption = "키워드로 사용자 추출"
        .OnAction = "ExtractCommitUsersWithKeyword"
        .Style = msoButtonCaption
    End With
    
    ' CSV로 내보내기
    Set menuItem = newMenu.Controls.Add(Type:=msoControlButton, Temporary:=True)
    With menuItem
        .Caption = "매핑 템플릿 CSV로 내보내기"
        .OnAction = "ExportToCSV"
        .Style = msoButtonCaption
    End With
    
    MsgBox "커밋사용자관리 메뉴가 추가되었습니다." & vbCrLf & _
           "상단 메뉴바에서 '커밋사용자관리'를 클릭하여 기능을 사용할 수 있습니다.", vbInformation
    
End Sub

' 이 매크로는 자동으로 실행될 수 있도록 ThisWorkbook 모듈에 추가하는 것이 좋습니다
' 아래는 워크북이 열릴 때 자동으로 메뉴를 추가하는 코드입니다
'
' Private Sub Workbook_Open()
'    CreateRibbonMenu
' End Sub