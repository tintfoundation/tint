var tintChatApp = angular.module('tintChatApp', ['ui.bootstrap', 'tint']);

tintChatApp.directive('ngEnter', function() {
			 return function(scope, element, attrs) {
			    element.bind("keydown keypress", function(event) {
					    if(event.which === 13) {
					       scope.$apply(function(){
							       scope.$eval(attrs.ngEnter, {'event': event});
							    });
					       
					       event.preventDefault();
					    }
					 });
			 };
		      });

tintChatApp.controller('FriendsListCtrl', ["$scope", "$http", "tint.app", function($scope, $http, app) {
			  $http.get('/api/v1/keys').success(function(data) {
							       $scope.friends = data.authorized_keys;
							       $scope.myId = data.mykey.id;
							       $scope.myStorage = app.init($scope.myId, $scope.myId, 'chat');
							    });
			  $scope.messages = [];
			  $scope.startChat = function(friend) {
			     $scope.friend = friend;
			     $scope.outbox = app.init(friend.id, $scope.myId, 'chat');
			     $scope.inbox = app.init($scope.myId, friend.id, 'chat');
			     $scope.inbox.ls('in', 0, 100, function(msgs) {
						$scope.messages = [];
						for(var i=0; i < msgs.length; i++) {
						   $scope.messages.push({ source: friend.name, value: msgs[i].value });
						}
					     });
			  };
			  $scope.send = function() {
			     if($scope.message == "") return;
			     $scope.messages.push({ source: 'me', value: $scope.message });
			     $scope.myStorage.push('out/' + $scope.friend.id, $scope.message);
			     $scope.outbox.push('in', $scope.message);
			     $scope.message = "";
			  };
		       }]);

tintChatApp.controller('AppsListCtrl', function($scope, $http) {
			   $http.get('/api/v1/apps').success(function(data) {
								$scope.apps = data;
							     });
			});