bootstrapAlert = function() {}
bootstrapAlert.warning = function(message) {
    $('#alertPlaceholder').html('<div class="alert"><span>'+message+'</span></div>')
}
bootstrapAlert.error = function(message) {
    $('#alertPlaceholder').html('<div class="alert alert-danger alert-dismissible fade show"><div style="font-weight: 200;"><i class="bi bi-exclamation-triangle-fill" style="margin-right: 10px;"></i>'+ message + '</div> <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>')
}

editModalError = function(message) {
    $('#editModalAlertPlaceholder').html('<div class="alert alert-danger alert-dismissible fade show"><div style="font-weight: 200;">'+ message + '</div> <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>')
}

accountModalError = function(message) {
    $('#accountModalAlertPlaceholder').html('<div class="alert alert-danger alert-dismissible fade show"><div style="font-weight: 200;">'+ message + '</div> <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>')
}

passwordModalError = function(message) {
    $('#passwordModalAlertPlaceholder').html('<div class="alert alert-danger alert-dismissible fade show"><div style="font-weight: 200;">'+ message + '</div> <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>')
}

var lastLen;
function Expand(obj){
    
    // var width = obj.offsetWidth // 329 -> 498
    // var parentWidth = document.getElementById("editFileModalContent").offsetWidth;
    // if (width / parentWidth >= 0.66 && obj.value.length >= lastLen)
    //     return;

    // console.log(width + " " + parentWidth)
    // obj.size = parseInt(obj.value.length);
    // lastLen = obj.value.length;

    if (obj.value.length < 31) {
        obj.size = obj.value.length;
    } else 
        obj.size = 31;
}

// Dashboard search function
function dashboardSearch() {
    var input = document.getElementById("dashSearch");
    var table = document.getElementById("dashTable");
    var filter = input.value.toUpperCase();

    // Get each table row so that we can loop
    var tableRow = table.getElementsByTagName("tr")

    for (i = 0; i < tableRow.length; i++) {
        var element = tableRow[i].getElementsByTagName("td")[0];

        if (element) {
            txtValue = element.textContent || element.innerText;

            if (txtValue.toUpperCase().indexOf(filter) > -1)
                tableRow[i].style.display = "";
            else 
                tableRow[i].style.display = "none";    
        }
    }
}

function findDelete() {
    var delButton = $('#deleteFileButton');
    var url = document.getElementById("fileUrl");
    url.select();
    url.setSelectionRange(0, 99999); /* For mobile devices */

    delButton.click(function () {
        globalThis.noerror = true;
        fetch('/api/delete/' + String(url.value).split("/").pop(), { method: 'DELETE' });
        $("#editFileModal").hide();
        $("#spinner").show();
        // signal call to ajaxStop to reload after all calls are made
        setTimeout(() => {$.ajax({}); }, 700); // wait half a second for remote database to update
    });
}

function verify(user) {
    console.log(user);
    var code = $("#code").val();
    globalThis.noerror = true;
    $.ajax({
        url: "/api/verify",
        type: "POST",
        crossDomain: true,
        data: user + " " + code,
        cache: false,
        dataType: "text",
        contentType: false,
        processData: false,
        success: function(data, textStatus, jqXHR) {
            if (data['error']) {
                editModalError(data['error']);
                globalThis.noerror = false;
            }
        }
    });
//    e.preventDefault(); //STOP default action
}

function reset() {
    var email = $("#resetEmail").val();
    globalThis.noerror = true;
    $.ajax({
        url: "/reset",
        type: "POST",
        crossDomain: true,
        data: email,
        cache: false,
        dataType: "text",
        contentType: false,
        processData: false,
        success: function(data, textStatus, jqXHR) {
            if (data['error']) {
                editModalError(data['error']);
                globalThis.noerror = false;
            }
        }
    });
//    e.preventDefault(); //STOP default action
}

function changeTag() {
	var url = document.getElementById("fileUrl");
	url.select();
	url.setSelectionRange(0, 99999);

	globalThis.noerror = true;
	$.ajax({
		url: "/api/updateCustomTag/" + String(url.value).split('/').pop(),
		type: "POST",
		crossDomain: true,
		data: $("#editCustomTag").val(),
		cache: false,
		dataType: "json",
		contentType: false,
		processData: false,
		success: function(data, textStatus, jqXHR) {
			if (data['error']) {
				editModalError(data['error']);
				globalThis.noerror = false;
			}
		}
	});
	e.preventDefault(); //STOP default action	
}

function toggleAccountView() {
    $('#v-pills-account-tab').click(function(){
        $('#v-pills-settings').hide();
        $('#v-pills-account').show();
        $('#editAccountInfoForm').hide();
        $('#editButton').show();
        $('#plans').hide();
    });
    $('#v-pills-settings-tab').click(function(){
        $('#v-pills-account').hide();
        $('#v-pills-settings').show();
        $('#editAccountInfoForm').hide();
        $('#editButton').hide();
        $('#plans').hide();
    });
}

function download(filename, textInput) {
    var element = document.createElement('a');
    element.setAttribute('href','data:text/plain;charset=utf-8, ' + encodeURIComponent(textInput));
    element.setAttribute('download', filename);
    document.body.appendChild(element);
    element.click();
    //document.body.removeChild(element);
}

function resizeDims(window) {
    if ($(window).width() <= 570) {
        $("#dateModifiedHeader").hide();
        $(".dateUpdatedContent").hide();
        $("#sizeHeader").hide();
        $(".sizeContent").hide();
    } else {
        $("#dateModifiedHeader").show();
        $(".dateUpdatedContent").show();
        $("#sizeHeader").show();
        $(".sizeContent").show();
    }

    $(".filess-table-row").each(function() {
        var row = $(this);
        var width = row.width() / 10;
        var element = row.find("p");
        var text = row.parent().data("filename");

        if (text.length > width) {
            element.html(text.substring(0, width - 5)+"...");
        } else {
            element.html(text);
        };
    });
}

$(window).resize(function() {
    resizeDims(window)
});

function hideEdit() {
    $("#modalFileName").show()
    $("#editFileNameButton").show()
    $("#editFileForm").hide()
}

$(document).ready(function() {
    // Get Stripe publishable key
    fetch("/api/config")
    .then((result) => { return result.json(); })
    .then((data) => {
      // Initialize Stripe.js
      const stripe = Stripe(data.publicKey);

      // Event handler
      document.querySelector("#tier2_signup").addEventListener("click", () => {
        // Get Checkout Session ID
        fetch("/create-checkout-session/tier2")
        .then((result) => { return result.json(); })
        .then((data) => {
          console.log(data);
          // Redirect to Stripe Checkout
          return stripe.redirectToCheckout({sessionId: data.sessionId})
        })
        .then((res) => {
          console.log(res);
        });
      });

      // Event handler
      document.querySelector("#tier3_signup").addEventListener("click", () => {
        // Get Checkout Session ID
        fetch("/create-checkout-session/tier3")
        .then((result) => { return result.json(); })
        .then((data) => {
          console.log(data);
          // Redirect to Stripe Checkout
          return stripe.redirectToCheckout({sessionId: data.sessionId})
        })
        .then((res) => {
          console.log(res);
        });
      });

      // Event handler
      document.querySelector("#tier4_signup").addEventListener("click", () => {
        // Get Checkout Session ID
        fetch("/create-checkout-session/tier4")
        .then((result) => { return result.json(); })
        .then((data) => {
          console.log(data);
          // Redirect to Stripe Checkout
          return stripe.redirectToCheckout({sessionId: data.sessionId})
        })
        .then((res) => {
          console.log(res);
        });
      });
    });

    resizeDims(window)
    console.log("Screen width:" + screen.width);

//    if (screen.width < 1000) {
//        console.log("life is unfair")
//        $(document).find($("#pricingPlan1")).attr("class", "pricing_row-sm-3");
//        $(document).find($("#pricingPlan2")).attr("class", "pricing_row-sm-3");
//        $(document).find($("#pricingPlan3")).attr("class", "pricing_row-sm-3");
//        $(document).find($("#tier3Text")).html("Tier 3 - BEST VALUE");
//        $(document).find($("#pricingPlan4")).attr("class", "pricing_row-sm-3");
//        $(document).find($(".breakspace")).html("<br>");
//    };

    $("#editFileModal").on('show.bs.modal', function (event) { // 42
        var button = $(event.relatedTarget) // Button that triggered the modal
        var userId = button.data('userid')
        var fileName = button.data('filename')
        var date = button.data('date')

        var subdomain = button.data('subdomain')
		if (button.data('tag') == 'None') {
			var tag = ''
		} else {
			var tag = button.data('tag')
		}

        var isImage = button.data('type') == "image"
        var isVideo = button.data('type') == "video"

        var urlLoc = 'https://filessstorage.s3.amazonaws.com/'+ userId + '/' + fileName
        if (tag !== 'None' && tag !== '') {
            if (subdomain !== 'None' && subdomain !== ''){
                var url = location.protocol + '//' + subdomain + '.' + window.location.host + '/' + tag + '/' + fileName
            } else {
                var url = location.protocol + '//' + window.location.host + '/' + userId + '/' + tag + '/' + fileName
            }
        } else {
            if (subdomain !== 'None' && subdomain !== ''){
                var url = location.protocol + '//' + subdomain + '.' + window.location.host + '/' + fileName
            } else {
                var url = location.protocol + '//' + window.location.host + '/' + userId + '/' + fileName
            }
        }

        var modal = $(this)
        if (isImage) {
            $("#videoContainer").hide();
            $("#thumbnailLink").show();
            modal.find($("#thumbnailLink")).attr('href', userId + '/' + fileName)
            modal.find($("#thumbnail")).attr('src', urlLoc)
        } else if (isVideo) {
            $("#thumbnailLink").hide();
            $("#videoContainer").show();

            modal.find($("#videoSource")).attr('src', urlLoc);
            document.getElementById('videoContainer').load();
        } else {
            $("#videoContainer").hide();
            $("#thumbnailLink").hide();
        }

        modal.find($("#fileUrl")).val(url);
        modal.find($("#editFileName")).val(fileName.split('.')[0]);
		modal.find($("#editCustomTag")).val(tag);

        if (parseInt(fileName.split('.')[0].length) < 31) {
            modal.find($("#editFileName")).attr("size",  parseInt(fileName.split('.')[0].length));
        } else
            modal.find($("#editFileName")).attr("size",  31);

        if (fileName.length > 29) {
            modal.find($("#modalFileName")).html(fileName.substring(0, 26) + "...");
        } else {
            modal.find($("#modalFileName")).html(fileName);
        };

        modal.find($("#dateTime")).html('<i class="bi bi-calendar-event" style="margin-right: 5px;"></i>' + date);
        modal.find($("#editFileFormType")).html('.' + fileName.split('.')[fileName.split('.').length - 1]);

        //document.getElementById("#editFileName").style = ((document.getElementById("#editFileName").value.length + 1) * 8) + 'px';;
        //modal.find($("#editFileName")).attr("style", $("#editFileName").attr("style") + " inline-size: " + (fileName.split('.')[0].length + 2) * 10 + "px;");
        var size = parseInt(fileName.length - fileName.split('.')[fileName.split('.').length - 1].length);
//        var size = parseInt(fileName.split('.')[0].length)
        if (size <= 30) {
            modal.find($("#editFileName")).attr("size", size);
        };

        $("#rejectEditButton").click(hideEdit);
        $("#confirmEditButton").click(function(e) {
            globalThis.noerror = true;
            $("#spinner").show();
            $.ajax({
                url: "/api/update/" + fileName,
                type: "POST",
                crossDomain: true,
                data: $("#editFileName").val() + $("#editFileFormType").html(),
                cache: false,
                dataType: "json",
                contentType: false,
                processData: false,
                success: function(data, textStatus, jqXHR) {
                    $("#spinner").hide();
                    if (data['error']) {
                        editModalError(data['error']);
                        globalThis.noerror = false;
                    }
                }
            });
            e.preventDefault(); //STOP default action
        });
    });

    $('#editFileModal').on('hidden.bs.modal', function (event) {
        document.getElementById('videoContainer').pause();
        hideEdit()
    });
    $('input[type="file"]').change(function() {console.log("changed"); $("#searchForm").submit(); });

    $("#fileCopy").click(function() {
        /* Get the text field */
        var copyText = document.getElementById("fileUrl");

        /* Select the text field */
        copyText.select();
        copyText.setSelectionRange(0, 99999); /* For mobile devices */
        /* Copy the text inside the text field */
        navigator.clipboard.writeText(copyText.value);

        $("#fileCopy").tooltip('enable')
        $("#fileCopy").tooltip('show')
    });

    $("#searchForm").submit(function(e) {
        var formData = new FormData($(this)[0]);
        console.log("FormData:" + formData);
        globalThis.noerror = true;
        $("#spinner").show();

        $.ajax({
            url: "/api/upload",
            type: "POST",
            crossDomain: true,
            data: formData,
            cache: false,
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data, textStatus, jqXHR) {
                $("#spinner").hide();
                if (data['error']) {
                    bootstrapAlert.error(data['error']);
                    globalThis.noerror = false;
                }
            }
        });
        e.preventDefault(); //STOP default action
    });

    $("#editSubdomain").on("keydown", function changeSubdomain(e) {
        if (e.keyCode == 13) {
            globalThis.noerror = true;
            $.ajax({
                url: "/api/updateSubdomain",
                type: "POST",
                crossDomain: true,
                data: $(this).val(),
                cache: false,
                dataType: "json",
                contentType: false,
                processData: false,
                success: function(data, textStatus, jqXHR) {
                    globalThis.noerror = false;
                    if (data['error']) {
                        accountModalError(data['error']);
                    }
                    stripe = Stripe("pk_live_51LF5v8GFIPLuPQxwVM73tF7OnkSPEpbPraRila8wFxTwQYSvO7G5BsqDPh5Dx63ouFS3N1aP7DZHKjw1o7tPo8Ge00ZtU2FMjL");
                    return stripe.redirectToCheckout({sessionId: data.sessionId});
                }
            });
            e.preventDefault(); //STOP default action
        }
    });

    $("#editFileNameButton").click(function(){
        $("#modalFileName").hide()
        $("#editFileNameButton").hide()
        $("#editFileForm").attr("style", $("#editFileForm").attr("style") + " display: flex;")
    });

    $("#passwordVerification").on("keydown", function checkPass(e){
        if (e.keyCode == 13) {
            var passwordInput = document.getElementById("passwordVerification").value;
            var email = document.getElementById("email").value;
            var fname = document.getElementById("fname").value;
            var lname = document.getElementById("lname").value;
            var pass1 = document.getElementById("pass1").value;
            var pass2 = document.getElementById("pass2").value;
            globalThis.noerror = true;

            $.ajax({
                url: "/updateAccountInformation",
                type: "POST",
                crossDomain: true,
                data: [email, fname, lname, pass1, pass2, passwordInput],
                cache: false,
                dataType: "json",
                contentType: false,
                processData: false,
                success: function(data, textStatus, jqXHR) {
                    if (data['error']) {
                        passwordModalError(data['error']);
                        globalThis.noerror = false;
                    }
                }
            });
            e.preventDefault(); //STOP default action
        }
    });

    $(".editAccountInfo").click(function(){
        $("#v-pills-account").toggle()
        $("#editAccountInfoForm").toggle()
        $("#editButton").toggle()
    });

    $(".planToggleButton").click(function(){
        $("#v-pills-settings").toggle()
        $("#plans").toggle()
    });

    findDelete()
    toggleAccountView()
});

function outFunc() {
    $("#fileCopy").tooltip('hide')
    $("#fileCopy").tooltip('disable')
}

$(document).ajaxStop(function(){  // builtin ajax function, called after all ajax requests are sent
//    window.location.reload();
    if (noerror) {
        window.location.reload();  // reload page after functions execute
    }
    globalThis.noerror = true
});