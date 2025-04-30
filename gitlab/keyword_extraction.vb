Sub ExtractCommitUsersWithKeyword()
    ' sksdu_ 키워드가 포함된 모든 commit_user 값을 추출하여 새 시트에 중복 제거 후 표시
    
    Dim ws As Worksheet
    Dim wsResult As Worksheet
    Dim lastRow As Long, lastCol As Long
    Dim i As Long, j As Long, resultRow As Long
    Dim cellValue As String
    Dim dict As Object
    Dim header As String
    Dim commitUserCols As New Collection
    
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
    wsResult.Cells(1, 2) = "출처 컬럼"
    wsResult.Cells(1, 3) = "출처 행"
    
    ' 헤더 서식 지정
    With wsResult.Range("A1:C1")
        .Font.Bold = True
        .Interior.Color = RGB(200, 200, 200)
    End With
    
    ' 초기 결과 행 설정
    resultRow = 2
    
    ' 진행 상황 표시
    Application.ScreenUpdating = False
    Application.StatusBar = "데이터 검색 중..."
    
    ' 모든 commit_user 컬럼에서 'sksdu_' 포함된 값 찾기
    For Each colIndex In commitUserCols
        For i = 2 To lastRow  ' 첫 번째 행은 헤더라고 가정
            cellValue = ws.Cells(i, colIndex).Value
            
            ' 빈 셀이 아니고 'sksdu_' 포함된 경우
            If Len(cellValue) > 0 And InStr(1, cellValue, "sksdu_", vbTextCompare) > 0 Then
                ' 중복 체크 및 추가
                If Not dict.Exists(cellValue) Then
                    dict.Add cellValue, 1
                    
                    ' 결과 시트에 추가
                    wsResult.Cells(resultRow, 1) = cellValue
                    wsResult.Cells(resultRow, 2) = ws.Cells(1, colIndex).Value
                    wsResult.Cells(resultRow, 3) = i
                    resultRow = resultRow + 1
                End If
            End If
        Next i
        
        ' 진행 상황 업데이트
        Application.StatusBar = "처리 중: " & colIndex & "/" & lastCol & " 컬럼 완료"
    Next colIndex
    
    ' 결과 요약
    wsResult.Cells(resultRow + 1, 1) = "총 " & dict.Count & "개의 고유 사용자 ID가 추출되었습니다."
    wsResult.Cells(resultRow + 1, 1).Font.Bold = True
    
    ' 컬럼 자동 맞춤
    wsResult.Columns("A:C").AutoFit
    
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
    
    For Each key In dict.Keys
        wsResult.Cells(mapRow, 1) = key
        mapRow = mapRow + 1
    Next key
    
    ' 매핑 템플릿 컬럼 자동 맞춤
    wsResult.Columns("A:C").AutoFit
    
    ' 상태 표시줄 초기화 및 화면 업데이트 다시 활성화
    Application.StatusBar = False
    Application.ScreenUpdating = True
    
    ' 결과 시트 활성화
    wsResult.Activate
    
    ' 완료 메시지
    MsgBox "추출 완료: " & dict.Count & "개의 고유 사용자 ID가 추출되었습니다." & vbCrLf & _
           "결과는 '추출된사용자' 시트에 있습니다.", vbInformation
           
End Sub

Sub ExportExtractedUsersToCSV()
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
