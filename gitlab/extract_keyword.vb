Sub FindKeywordAndListUnique()
    Dim ws As Worksheet
    Dim cell As Range
    Dim keyword As String
    Dim dict As Object
    Dim resultRow As Long
    Dim foundStr As String
    
    keyword = "sksdu_"
    Set dict = CreateObject("Scripting.Dictionary")
    Set ws = ActiveSheet
    
    ' 워크시트의 모든 셀을 검색
    For Each cell In ws.UsedRange
        If Not IsEmpty(cell.Value) Then
            If InStr(cell.Value, keyword) > 0 Then
                ' 셀의 내용 중 keyword가 포함된 전체 텍스트를 dict에 추가
                foundStr = ExtractKeywordWithSuffix(cell.Value, keyword)
                If Not dict.exists(foundStr) Then
                    dict.Add foundStr, 1
                End If
            End If
        End If
    Next cell
    
    ' 결과를 새로운 시트에 출력
    Dim resultSheet As Worksheet
    Set resultSheet = Worksheets.Add
    resultSheet.Name = "Unique_Keywords"
    
    resultRow = 1
    Dim key As Variant
    For Each key In dict.Keys
        resultSheet.Cells(resultRow, 1).Value = key
        resultRow = resultRow + 1
    Next key

    MsgBox "완료되었습니다. " & dict.Count & "개의 고유 항목이 발견되었습니다."
End Sub

Function ExtractKeywordWithSuffix(text As String, keyword As String) As String
    ' keyword로 시작하는 패턴을 추출 (예: sksdu_1234)
    Dim regex As Object
    Set regex = CreateObject("VBScript.RegExp")
    With regex
        .Pattern = keyword & "[A-Za-z0-9_]+"
        .Global = True
    End With
    
    If regex.test(text) Then
        ExtractKeywordWithSuffix = regex.Execute(text)(0)
    Else
        ExtractKeywordWithSuffix = ""
    End If
End Function
