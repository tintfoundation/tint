var tintStorage = angular.module('tintStorage', []);
/*
tintStorage.factory('get', ['$http', function($http) {
			       return function(key, callback) {
				  callback("result of get is " + key);
			       };
			    }]);
*/

tintStorage.factory('get', function() { return { something: 'hi' }; });

var tintChatApp = angular.module('tintChatApp', ['ui.bootstrap']);

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

tintChatApp.controller('FriendsListCtrl', ["$scope", "$http", function($scope, $http) {
			  $http.get('/api/v1/keys').success(function(data) {
							       $scope.friends = data.authorized_keys;
							    });
			  $scope.messages = [];
			  $scope.startChat = function(friend) {
			     $scope.friend = friend;
			     $scope.messages = [ {source: 'billy', value: "hi there"}, {source: 'billy two', value: "hi there again"} ];
			  };
			  $scope.send = function() {
			     if($scope.message != "")
				$scope.messages.push({ source: 'me', value: $scope.message });
			     $scope.message = "";
			     //console.log(angular.module('tintStorage')); //
			     get('akey', function(r) { alert(r); });
			  };
		       }]);

tintChatApp.controller('AppsListCtrl', function($scope, $http) {
			   $http.get('/api/v1/apps').success(function(data) {
								$scope.apps = data;
							     });
			});