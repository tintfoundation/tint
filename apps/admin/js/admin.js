var phonecatApp = angular.module('tintAdminApp', []);

phonecatApp.controller('FriendsListCtrl', function ($scope, $http) {
			  $http.get('/api/v1/keys').success(function(data) {
							       $scope.friends = data.authorized_keys;
							    });
			  $scope.removeFriend = function(index) {
			     $http.delete('/api/v1/keys', { params: { name: $scope.friends[index].name } });
			     $scope.friends.splice(index, 1);
			  };
		       });