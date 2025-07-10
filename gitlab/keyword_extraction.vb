Sub ExtractNonStandardUsers()
    ' 인사DB 형식(이름(아이디))이 아닌 모든 commit_user 값을 추출
    
    Dim ws As Worksheet
    Dim wsResult As Worksheet
    Dim lastRow As Long, lastCol As Long
    Dim i As Long, colIndex As Long, resultRow As Long
    Dim cellValue As String
    Dim userDict As Object
    Dim header As String
    
    ' 딕셔너리 생성 (중복 제거용)
    Set userDict = CreateObject("Scripting.Dictionary")
    
    ' 현재 활성 시트
    Set ws = ActiveSheet
    
    ' 마지막 행과 열 찾기
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    
    ' 결과 시트 생성
    On Error Resume Next
    Application.DisplayAlerts = False
    Worksheets("비표준사용자").Delete
    Application.DisplayAlerts = True
    On Error GoTo 0
    
    Set wsResult = Worksheets.Add(After:=Worksheets(Worksheets.Count))
    wsResult.Name = "비표준사용자"
    
    ' 헤더 추가
    wsResult.Cells(1, 1) = "사용자 ID"
    wsResult.Cells(1, 2) = "패턴 유형"
    wsResult.Cells(1, 3) = "출처 컬럼"
    wsResult.Cells(1, 4) = "출처 행"
    
    ' 헤더 서식
    wsResult.Range("A1:D1").Font.Bold = True
    wsResult.Range("A1:D1").Interior.Color = RGB(200, 200, 200)
    
    resultRow = 2
    
    ' 진행 표시
    Application.ScreenUpdating = False
    Application.StatusBar = "검색 중..."
    
    ' commit_user 컬럼 찾기 및 처리
    For colIndex = 1 To lastCol
        header = ws.Cells(1, colIndex).Value
        
        If InStr(1, header, "commit_user", vbTextCompare) > 0 Then
            ' 이 컬럼이 commit_user 컬럼임
            For i = 2 To lastRow
                cellValue = Trim(ws.Cells(i, colIndex).Value)
                
                ' 빈 셀이 아니고 표준 형식이 아닌 경우만 처리
                If Len(cellValue) > 0 And Not IsStandardFormat(cellValue) Then
                    ' 중복 확인 후 추가
                    If Not userDict.Exists(cellValue) Then
                        userDict.Add cellValue, GetPatternType(cellValue)
                        
                        ' 결과 시트에 추가
                        wsResult.Cells(resultRow, 1) = cellValue
                        wsResult.Cells(resultRow, 2) = GetPatternType(cellValue)
                        wsResult.Cells(resultRow, 3) = header
                        wsResult.Cells(resultRow, 4) = i
                        resultRow = resultRow + 1
                    End If
                End If
            Next i
        End If
    Next colIndex
    
    ' 매핑 템플릿 추가
    wsResult.Cells(resultRow + 2, 1) = "매핑 템플릿:"
    wsResult.Cells(resultRow + 2, 1).Font.Bold = True
    
    wsResult.Cells(resultRow + 3, 1) = "AS-IS"
    wsResult.Cells(resultRow + 3, 2) = "TO-BE"
    wsResult.Cells(resultRow + 3, 3) = "비고"
    
    wsResult.Range(wsResult.Cells(resultRow + 3, 1), wsResult.Cells(resultRow + 3, 3)).Font.Bold = True
    wsResult.Range(wsResult.Cells(resultRow + 3, 1), wsResult.Cells(resultRow + 3, 3)).Interior.Color = RGB(200, 200, 200)
    
    ' 추출된 사용자를 템플릿에 추가
    resultRow = resultRow + 4
    For Each key In userDict.Keys
        wsResult.Cells(resultRow, 1) = key
        wsResult.Cells(resultRow, 3) = userDict(key)
        resultRow = resultRow + 1
    Next key
    
    ' 열 너비 조정
    wsResult.Columns("A:D").AutoFit
    
    ' 화면 업데이트 복원
    Application.StatusBar = False
    Application.ScreenUpdating = True
    
    ' 결과 시트 활성화
    wsResult.Activate
    
    ' 완료 메시지
    MsgBox "총 " & userDict.Count & "개의 비표준 형식 사용자가 추출되었습니다.", vbInformation
End Sub

Function IsStandardFormat(value As String) As Boolean
    ' 표준 형식(이름(아이디)) 확인
    
    ' 괄호가 있는지 확인
    Dim openPos As Integer, closePos As Integer
    
    openPos = InStr(1, value, "(")
    closePos = InStr(1, value, ")")
    
    ' 괄호 쌍이 있고, 열린 괄호가 닫힌 괄호보다 앞에 있으며, 닫힌 괄호가 문자열 끝에 있는 경우
    If openPos > 1 And closePos > openPos And closePos = Len(value) Then
        ' 이름 부분이 있고 내용 부분도 있는 경우만 표준 형식으로 간주
        If openPos > 1 And closePos - openPos > 1 Then
            IsStandardFormat = True
            Exit Function
        End If
    End If
    
    IsStandardFormat = False
End Function

Function GetPatternType(value As String) As String
    ' 비표준 형식의 패턴 분석
    
    ' 이메일 형식 확인
    If InStr(1, value, "@") > 0 Then
        GetPatternType = "이메일"
        Exit Function
    End If
    
    ' sksdu_ 형식 확인
    If InStr(1, value, "sksdu_", vbTextCompare) > 0 Then
        GetPatternType = "사번ID"
        Exit Function
    End If
    
    ' 도메인 계정 형식 확인
    If InStr(1, value, "\") > 0 Then
        GetPatternType = "도메인계정"
        Exit Function
    End If
    
    ' 한글 이름만 있는 경우 (2-5자)
    If Len(value) >= 2 And Len(value) <= 5 Then
        Dim isKorean As Boolean
        isKorean = True
        
        Dim j As Integer
        For j = 1 To Len(value)
            If Asc(Mid(value, j, 1)) < 128 Then
                isKorean = False
                Exit For
            End If
        Next j
        
        If isKorean Then
            GetPatternType = "한글이름"
            Exit Function
        End If
    End If
    
    ' 영문 이름 확인 (공백 포함)
    Dim isEnglish As Boolean
    isEnglish = True
    
    For j = 1 To Len(value)
        Dim char As String
        char = Mid(value, j, 1)
        
        If Not (char >= "A" And char <= "Z") And _
           Not (char >= "a" And char <= "z") And _
           Not (char = " ") Then
            isEnglish = False
            Exit For
        End If
    Next j
    
    If isEnglish Then
        GetPatternType = "영문이름"
        Exit Function
    End If
    
    ' 기타 형식
    GetPatternType = "기타"
End Function

Sub ExportMappingToCSV()
    ' 추출된 매핑 템플릿을 CSV 파일로 내보내기
    
    Dim wsResult As Worksheet
    Dim filePath As String
    Dim startRow As Long, lastRow As Long
    Dim i As Long
    
    ' 결과 시트 확인
    On Error Resume Next
    Set wsResult = Worksheets("비표준사용자")
    On Error GoTo 0
    
    If wsResult Is Nothing Then
        MsgBox "비표준사용자 시트가 없습니다. 먼저 ExtractNonStandardUsers를 실행하세요.", vbExclamation
        Exit Sub
    End If
    
    ' 매핑 템플릿 위치 찾기
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
    
    ' 저장 경로 설정
    filePath = Application.DefaultFilePath & "\commit_user_mapping.csv"
    
    ' 저장 대화상자
    filePath = Application.GetSaveAsFilename( _
        InitialFileName:="commit_user_mapping.csv", _
        FileFilter:="CSV 파일 (*.csv), *.csv", _
        Title:="매핑 파일 저장")
    
    If filePath = "False" Then
        MsgBox "저장이 취소되었습니다.", vbInformation
        Exit Sub
    End If
    
    ' 마지막 행 찾기
    lastRow = startRow
    Do While wsResult.Cells(lastRow + 1, 1).Value <> ""
        lastRow = lastRow + 1
        If lastRow > 10000 Then Exit Do  ' 안전 장치
    Loop
    
    ' CSV 저장
    Dim fso As Object, ts As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set ts = fso.CreateTextFile(filePath, True)
    
    ' 헤더
    ts.WriteLine "AS-IS,TO-BE,비고"
    
    ' 데이터
    For i = startRow + 1 To lastRow
        Dim asIs As String, toBe As String, note As String
        
        asIs = wsResult.Cells(i, 1).Value
        toBe = wsResult.Cells(i, 2).Value
        note = wsResult.Cells(i, 3).Value
        
        ' 특수 문자 처리
        asIs = Replace(asIs, """", """""")
        If InStr(1, asIs, ",") > 0 Then asIs = """" & asIs & """"
        
        If toBe <> "" Then
            toBe = Replace(toBe, """", """""")
            If InStr(1, toBe, ",") > 0 Then toBe = """" & toBe & """"
        End If
        
        If note <> "" Then
            note = Replace(note, """", """""")
            If InStr(1, note, ",") > 0 Then note = """" & note & """"
        End If
        
        ts.WriteLine asIs & "," & toBe & "," & note
    Next i
    
    ts.Close
    
    MsgBox "매핑 템플릿이 저장되었습니다:" & vbCrLf & filePath, vbInformation
End Sub