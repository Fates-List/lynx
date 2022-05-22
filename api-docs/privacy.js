const downloadTextFile = (text, name) => {
    const a = document.createElement('a');
    const type = name.split(".").pop();
    a.href = URL.createObjectURL( new Blob([text], { type:`text/${type === "txt" ? "plain" : type}` }) );
    a.download = name;
    a.click();
}  

const dataRequest = async () => {
    let requestId = document.querySelector("#user-id").value
    document.querySelector("#request-btn").innerText = "Requesting..."

    let userData = user()

    let res = await fetch(`${userData.lynxUrl}/data?requested_id=${requestId}&origin_user_id=${userData.id}`, {
        method: "GET",
        headers: {
            Authorization: userData.token,
            'Content-Type': "application/json"
        }
    })
    let json = await res.json();
    if(!res.ok) {
        let reason = json.reason || json.detail || "Unknown error"
        console.log(reason)
        alert(reason)
        return
    }

    // Now keep polling for the task
    let got = false
    let task;
    while(!got) {
        task = await fetch(`${userData.lynxUrl}/long-running/${json.task_id}`)
        if(task.ok) {
            got = true
        }
    }
    let taskJson = await task.json()
    downloadTextFile(taskJson, `data-request-${requestId}.json`)

}
