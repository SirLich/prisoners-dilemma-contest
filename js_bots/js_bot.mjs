export function play(data) {
    // Convert stringified data into a json object
    data = JSON.parse(data)

    // You can log the results, to inspect what data you have
    console.log(data)

    // You can query the data, to form a complex strategy
    return data["self_score"] >= data["other_score"];
}

export function start(data) {
    return
}

export function getName() {
    return "JS Bot";
}