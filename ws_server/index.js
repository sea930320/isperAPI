var config = require('./config.json')
var express = require('express');
var XMLHttpRequest = require('xmlhttprequest').XMLHttpRequest;
var _ = require('lodash');

// host of the server
var host = config.api_host;
var port = config.api_port;

const app = express();

const server = app.listen(config.ws_port, function () {
    console.log('server running on port ' + config.ws_port);
});


const io = require('socket.io')(server);
// creating an instance of XMLHttpRequest
var xhttp = new XMLHttpRequest();

var onlineAllocs = []

// when a connection happens (client enters on the website)
io.on('connection', function (socket) {

    // if the event with the name 'message' comes from the client with the argument 'msgObject',
    // which is an object with the format: {'user_name': < name >, 'message': < message >},
    // it emits for every connected client that a message has been sent, sending the message to the event
    socket.on('userIsOnline', function (data) {
        if (!data.alloc_id) {
            return
        }
        console.log("----------------------new user connected---------------------")
        data.socket_id = socket.id
        console.log('param', data)
        console.log('before onlineAllocs', onlineAllocs)
        if (_.every(onlineAllocs, (alloc) => {
            return alloc.alloc_id != data.alloc_id
        })) {
            onlineAllocs.push(data)
        }
        console.log('onlineAllocs', onlineAllocs)
        io.emit('onlineAllocs', { 'allocs': onlineAllocs })
    })
    socket.on('disconnect', function () {
        console.log("----------------------user disconnected---------------------")
        console.log("socketID", socket.id)
        console.log('before onlineAllocs', onlineAllocs)
        var connectedId = _.findIndex(onlineAllocs, (alloc) => {
            return alloc.socket_id == socket.id
        })
        if (connectedId != -1) {
            onlineAllocs.splice(connectedId, 1)
        }
        console.log('after onlineAllocs', onlineAllocs)
        io.emit('onlineAllocs', { 'allocs': onlineAllocs })
    });
    // 'getMessage' in the client side
    socket.on('message', function (msgObject) {
        console.log(msgObject)
        io.emit('getMessage', {
            'result': msgObject
        });
    });

    // 'getStudentMessage' in the client side
    socket.on('student_message', function (msgObject) {
        console.log(msgObject)
        io.emit('getStudentMessage', {
            'result': msgObject
        });
    });

    // 'guiderMessage' in the client side
    socket.on('guider_message', function (msgObject) {
        console.log(msgObject)
        io.emit('getGuiderMessage', {
            'result': msgObject
        });
    });

});