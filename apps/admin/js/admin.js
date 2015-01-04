var tintAdminApp = angular.module('tintAdminApp', ['ui.bootstrap']);

tintAdminApp.controller('FriendsListCtrl', function($scope, $http) {
			   $http.get('/api/v1/keys').success(function(data) {
								$scope.friends = data.authorized_keys;
								$scope.myid = data.mykey.id;
								$scope.mykey = data.mykey.key;
							     });
			   $scope.removeFriend = function(index) {
			      $http.delete('/api/v1/keys', { params: { name: $scope.friends[index].name } });
			      $scope.friends.splice(index, 1);
			   };
			   
			   $scope.addFriend = function(friend) {
			      var r = $http.post('/api/v1/keys', {}, { params: friend });
			      r.success(function(data, status, headers, config) {
					   $scope.friends.push(friend);
					});
			      r.error(function(data, status, headers, config) {
					 alert(data.error);
				      });
			   };
			});

tintAdminApp.controller('AppsListCtrl', function($scope, $http) {
			   $http.get('/api/v1/apps').success(function(data) {
								$scope.apps = data;
							     });
			});