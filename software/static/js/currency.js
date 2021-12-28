const convert = (n1, n2, conversionFactor) => {
    let id1 = "cb" + n1; 
    let id2 = "cb" + n2;
    let inputBox = document.getElementById(id1).value;
    document.getElementById(id2).value = ((inputBox * conversionFactor).toFixed(2));
}
